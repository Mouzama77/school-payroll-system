"""Unit tests for leave_service.update_leave_status — Task 26.

Validates Design Properties 4 and 5:
  Property 4 (Leave Approval Coverage):
    When leave transitions to APPROVED, exactly one ON_LEAVE attendance record
    exists per calendar date in [start_date, end_date], except for dates where
    is_override=True which are left unchanged.
  Property 5 (Audit Log Atomicity):
    Every successful approval/rejection produces exactly one audit_logs row.
    If the transaction rolls back, no audit row is committed.

Uses SQLite in-memory DB (same pattern as Task 25).
"""

import uuid
from datetime import date, datetime, timedelta, timezone, time

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models.attendance import Attendance, AttendanceStatus
from app.models.audit_log import AuditLog
from app.models.department import Department
from app.models.employee import Employee
from app.models.leave import Leave, LeaveStatus, LeaveType
from app.models.role import Role
from app.models.user import User
from app.services.leave_service import update_leave_status


# ── In-memory SQLite engine ───────────────────────────────────────────────────

@pytest.fixture(scope="module")
def engine():
    from sqlalchemy.pool import StaticPool
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,   # ensures all sessions share the same in-memory DB
    )

    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# ── Factories ─────────────────────────────────────────────────────────────────

def make_role(db):
    r = Role(id=uuid.uuid4(), name=f"role_{uuid.uuid4().hex[:6]}", description=None,
             created_at=datetime.now(timezone.utc))
    db.add(r); db.flush(); return r


def make_dept(db):
    code = uuid.uuid4().hex[:8]
    d = Department(
        id=uuid.uuid4(), name=f"Dept_{uuid.uuid4().hex[:6]}",
        description=None, created_at=datetime.now(timezone.utc),
        code=code, is_active=True, updated_at=datetime.now(timezone.utc),
    )
    db.add(d); db.flush(); return d


def make_employee(db):
    r = make_role(db)
    dept = make_dept(db)
    e = Employee(
        id=uuid.uuid4(), first_name="Leave", last_name="Tester",
        email=f"leave_{uuid.uuid4().hex[:6]}@test.com",
        salary=30000.0, department_id=dept.id, role_id=r.id,
        reporting_time=time(9, 30),
    )
    db.add(e); db.flush(); return e


def make_user(db):
    u = User(
        id=uuid.uuid4(),
        email=f"user_{uuid.uuid4().hex[:6]}@test.com",
        password_hash="hashed", role="admin", is_active=True,
        must_change_password=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        registration_status="ACTIVE",
        email_verified=False,
    )
    db.add(u); db.flush(); return u


def make_pending_leave(db, employee_id, start_date, end_date, leave_type=LeaveType.CASUAL):
    leave = Leave(
        id=uuid.uuid4(),
        employee_id=employee_id,
        leave_type=leave_type,
        status=LeaveStatus.PENDING,
        start_date=start_date,
        end_date=end_date,
        reason="test",
    )
    db.add(leave); db.flush(); return leave


# ── Helper ────────────────────────────────────────────────────────────────────

def date_range(start, end):
    """Inclusive list of dates from start to end."""
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


# ── Task 26.2: Leave approval coverage (Design Property 4) ───────────────────

class TestLeaveApprovalCoverage:

    def test_approval_creates_on_leave_for_all_dates(self, db):
        """Approving a leave creates ON_LEAVE attendance for every date in range."""
        emp = make_employee(db)
        actor = make_user(db)
        start = date(2025, 7, 1)
        end = date(2025, 7, 3)  # 3 dates
        leave = make_pending_leave(db, emp.id, start, end)

        update_leave_status(db, leave.id, LeaveStatus.APPROVED, actor.id)

        for d in date_range(start, end):
            att = db.query(Attendance).filter(
                Attendance.employee_id == emp.id,
                Attendance.date == d,
            ).first()
            assert att is not None, f"No attendance for {d}"
            assert att.status == AttendanceStatus.ON_LEAVE, f"Wrong status for {d}: {att.status}"

    def test_approval_status_becomes_approved(self, db):
        """Leave record status is set to APPROVED."""
        emp = make_employee(db)
        actor = make_user(db)
        leave = make_pending_leave(db, emp.id, date(2025, 7, 10), date(2025, 7, 11))
        result = update_leave_status(db, leave.id, LeaveStatus.APPROVED, actor.id)
        assert result.status == LeaveStatus.APPROVED
        assert result.approved_by == actor.id

    def test_approval_skips_overridden_dates(self, db):
        """Dates where is_override=True are left untouched (Design Property 4)."""
        emp = make_employee(db)
        actor = make_user(db)
        start = date(2025, 8, 1)
        end = date(2025, 8, 3)

        # Pre-insert an overridden PRESENT record on 2025-08-02
        overridden_date = date(2025, 8, 2)
        overridden_att = Attendance(
            id=uuid.uuid4(), employee_id=emp.id, date=overridden_date,
            status=AttendanceStatus.PRESENT, is_override=True,
            override_reason="Manual override",
        )
        db.add(overridden_att); db.flush()

        leave = make_pending_leave(db, emp.id, start, end)
        update_leave_status(db, leave.id, LeaveStatus.APPROVED, actor.id)

        # 2025-08-02 must remain PRESENT (override respected)
        att_02 = db.query(Attendance).filter(
            Attendance.employee_id == emp.id, Attendance.date == overridden_date
        ).first()
        assert att_02.status == AttendanceStatus.PRESENT
        assert att_02.is_override is True

        # Other dates must be ON_LEAVE
        for d in [date(2025, 8, 1), date(2025, 8, 3)]:
            att = db.query(Attendance).filter(
                Attendance.employee_id == emp.id, Attendance.date == d
            ).first()
            assert att.status == AttendanceStatus.ON_LEAVE, f"{d} should be ON_LEAVE"

    def test_approval_updates_existing_non_overridden_attendance(self, db):
        """Existing non-overridden attendance on a leave day is updated to ON_LEAVE."""
        emp = make_employee(db)
        actor = make_user(db)
        d = date(2025, 9, 5)

        # Pre-existing PRESENT record (no override)
        existing = Attendance(
            id=uuid.uuid4(), employee_id=emp.id, date=d,
            status=AttendanceStatus.PRESENT, is_override=False,
        )
        db.add(existing); db.flush()

        leave = make_pending_leave(db, emp.id, d, d)
        update_leave_status(db, leave.id, LeaveStatus.APPROVED, actor.id)

        db.refresh(existing)
        assert existing.status == AttendanceStatus.ON_LEAVE

    def test_rejection_does_not_create_attendance(self, db):
        """Rejecting a leave must NOT create any ON_LEAVE attendance records."""
        emp = make_employee(db)
        actor = make_user(db)
        start = date(2025, 10, 1)
        end = date(2025, 10, 2)
        leave = make_pending_leave(db, emp.id, start, end)

        update_leave_status(db, leave.id, LeaveStatus.REJECTED, actor.id)

        for d in date_range(start, end):
            att = db.query(Attendance).filter(
                Attendance.employee_id == emp.id, Attendance.date == d
            ).first()
            assert att is None, f"Unexpected attendance for rejected leave on {d}"


# ── Task 26.2 / 26.3: Audit log atomicity (Design Property 5) ────────────────

class TestAuditLogAtomicity:

    def test_approval_writes_exactly_one_audit_log(self, db):
        """Approving a leave writes exactly one LEAVE_APPROVED audit log entry."""
        emp = make_employee(db)
        actor = make_user(db)
        leave = make_pending_leave(db, emp.id, date(2025, 11, 1), date(2025, 11, 1))

        update_leave_status(db, leave.id, LeaveStatus.APPROVED, actor.id)

        logs = db.query(AuditLog).filter(
            AuditLog.entity_id == leave.id,
            AuditLog.action == "LEAVE_APPROVED",
        ).all()
        assert len(logs) == 1
        assert logs[0].actor_id == actor.id
        assert logs[0].entity_type == "leave"

    def test_rejection_writes_exactly_one_audit_log(self, db):
        """Rejecting a leave writes exactly one LEAVE_REJECTED audit log entry."""
        emp = make_employee(db)
        actor = make_user(db)
        leave = make_pending_leave(db, emp.id, date(2025, 11, 5), date(2025, 11, 5))

        update_leave_status(db, leave.id, LeaveStatus.REJECTED, actor.id)

        logs = db.query(AuditLog).filter(
            AuditLog.entity_id == leave.id,
            AuditLog.action == "LEAVE_REJECTED",
        ).all()
        assert len(logs) == 1

    def test_rollback_removes_audit_log(self, db):
        """If the session rolls back, the audit log entry is also rolled back.

        Design Property 5: audit writes are part of the same transaction.
        """
        emp = make_employee(db)
        actor = make_user(db)
        leave = make_pending_leave(db, emp.id, date(2025, 12, 1), date(2025, 12, 1))

        # Manually append an audit log and then roll back — simulates transaction failure
        log_id = uuid.uuid4()
        db.add(AuditLog(
            id=log_id,
            actor_id=actor.id,
            action="LEAVE_APPROVED",
            entity_type="leave",
            entity_id=leave.id,
            detail="test rollback",
        ))
        db.flush()

        # Confirm it's visible inside the session before rollback
        found = db.query(AuditLog).filter(AuditLog.id == log_id).first()
        assert found is not None

        # Roll back — the audit log must disappear
        db.rollback()

        found_after = db.query(AuditLog).filter(AuditLog.id == log_id).first()
        assert found_after is None, "Audit log should have been rolled back"

    def test_rollback_removes_leave_status_change_and_audit_log(self, engine):
        """Design Property 5: if commit fails, BOTH the leave status change
        and the audit log row are rolled back together.

        Method (production-grade, multi-session):
        1. Session-1 commits leave as PENDING (durably stored in SQLite via StaticPool).
        2. Session-2 calls update_leave_status() with commit patched to raise RuntimeError.
           Service flushes, then patched commit raises → service calls rollback().
        3. Session-3 (brand-new) queries the leave and audit log.
           Leave must be PENDING; zero LEAVE_APPROVED audit logs.
        """
        from unittest.mock import patch
        from sqlalchemy.pool import StaticPool

        Session = sessionmaker(bind=engine)

        # ── Session 1: durably persist role, dept, emp, actor, leave ──────
        s1 = Session()
        r_id = uuid.uuid4()
        dept_id = uuid.uuid4()
        emp_id = uuid.uuid4()
        actor_id = uuid.uuid4()
        leave_id = uuid.uuid4()
        try:
            s1.add(Role(id=r_id, name=f"role_{r_id.hex[:6]}",
                        created_at=datetime.now(timezone.utc)))
            s1.flush()
            code = uuid.uuid4().hex[:8]
            s1.add(Department(id=dept_id, name=f"Dept_{dept_id.hex[:6]}",
                               created_at=datetime.now(timezone.utc),
                               code=code, is_active=True,
                               updated_at=datetime.now(timezone.utc)))
            s1.flush()
            s1.add(Employee(id=emp_id, first_name="RB", last_name="Test",
                             email=f"rb_{emp_id.hex[:6]}@test.com",
                             salary=30000.0, department_id=dept_id, role_id=r_id,
                             reporting_time=time(9, 30)))
            s1.flush()
            s1.add(User(id=actor_id, email=f"actor_{actor_id.hex[:6]}@test.com",
                        password_hash="h", role="admin", is_active=True,
                        must_change_password=False,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                        registration_status="ACTIVE", email_verified=False))
            s1.flush()
            s1.add(Leave(id=leave_id, employee_id=emp_id, leave_type=LeaveType.SICK,
                         status=LeaveStatus.PENDING,
                         start_date=date(2026, 3, 1), end_date=date(2026, 3, 1),
                         reason="rollback_test"))
            s1.commit()  # durably stored
        finally:
            s1.close()

        # ── Session 2: patch commit to raise after flush ──────────────────
        s2 = Session()
        try:
            def failing_commit():
                s2.flush()
                raise RuntimeError("Simulated commit failure — triggers rollback")

            with patch.object(s2, "commit", side_effect=failing_commit):
                try:
                    update_leave_status(s2, leave_id, LeaveStatus.APPROVED, actor_id)
                    pytest.fail("Expected RuntimeError to propagate")
                except (RuntimeError, Exception):
                    pass  # service wraps in HTTPException after rollback — both acceptable
        finally:
            s2.close()

        # ── Session 3: brand-new session, bypass identity map ─────────────
        s3 = Session()
        try:
            persisted_leave = s3.query(Leave).filter(Leave.id == leave_id).first()
            assert persisted_leave is not None, \
                "Leave record must still exist after rollback"
            assert persisted_leave.status == LeaveStatus.PENDING, (
                f"Leave must be PENDING after rollback, got {persisted_leave.status}"
            )

            audit_logs = s3.query(AuditLog).filter(
                AuditLog.entity_id == leave_id,
                AuditLog.action == "LEAVE_APPROVED",
            ).all()
            assert len(audit_logs) == 0, (
                f"Expected 0 LEAVE_APPROVED audit logs after rollback, got {len(audit_logs)}"
            )
        finally:
            s3.close()
