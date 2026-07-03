"""Unit tests for AttendanceService — Task 25.

Tests mark_attendance and override_attendance state machine transitions
as specified in Design §2.2 and Requirements 8.x.

Uses SQLite in-memory DB to avoid needing PostgreSQL.
"""

import uuid
from datetime import date, time, timedelta, timezone, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models.attendance import Attendance, AttendanceStatus
from app.models.employee import Employee
from app.models.user import User
from app.models.department import Department
from app.models.role import Role
from app.models.audit_log import AuditLog
from app.schemas.attendance import AttendanceCreate, AttendanceCreateStatus
from app.services.attendance_service import AttendanceService


# ── In-memory SQLite engine ───────────────────────────────────────────────────

@pytest.fixture(scope="module")
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    # SQLite does not enforce FK by default; enable it
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


# ── Shared test data factories ────────────────────────────────────────────────

def make_role(db):
    r = Role(id=uuid.uuid4(), name=f"role_{uuid.uuid4().hex[:6]}", description=None,
             created_at=datetime.now(timezone.utc))
    db.add(r); db.flush(); return r


def make_dept(db):
    unique_code = uuid.uuid4().hex[:8]
    d = Department(id=uuid.uuid4(), name=f"Dept_{uuid.uuid4().hex[:6]}",
                   description=None, created_at=datetime.now(timezone.utc),
                   code=unique_code, is_active=True, updated_at=datetime.now(timezone.utc))
    db.add(d); db.flush(); return d


def make_employee(db):
    role = make_role(db)
    dept = make_dept(db)
    e = Employee(
        id=uuid.uuid4(),
        first_name="Test", last_name="Emp",
        email=f"emp_{uuid.uuid4().hex[:6]}@test.com",
        salary=30000.0,
        department_id=dept.id,
        role_id=role.id,
        reporting_time=time(9, 30),
    )
    db.add(e); db.flush(); return e


def make_user(db):
    u = User(
        id=uuid.uuid4(),
        email=f"user_{uuid.uuid4().hex[:6]}@test.com",
        password_hash="hashed",
        role="admin",
        is_active=True,
        must_change_password=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        registration_status="ACTIVE",
        email_verified=False,
    )
    db.add(u); db.flush(); return u


def make_payload(employee_id, status=AttendanceCreateStatus.PRESENT, date_=None, check_in_time=None):
    return AttendanceCreate(
        employee_id=employee_id,
        date=date_ or date.today() - timedelta(days=1),
        status=status,
        check_in_time=check_in_time,
    )


# ── Task 25.2: mark_attendance transitions ────────────────────────────────────

class TestMarkAttendance:

    def test_new_record_returns_201_flag(self, db):
        """New attendance record → (Attendance, False) — caller returns 201."""
        emp = make_employee(db)
        actor = make_user(db)
        payload = make_payload(emp.id)
        result, was_update = AttendanceService.mark_attendance(db, payload, actor.id)
        assert was_update is False
        assert result.status == AttendanceStatus.PRESENT
        assert result.employee_id == emp.id

    def test_new_record_persists_check_in_time(self, db):
        """check_in_time is stored on the new record (Req 16.2)."""
        emp = make_employee(db)
        actor = make_user(db)
        cit = time(9, 45)
        payload = make_payload(emp.id, status=AttendanceCreateStatus.LATE, check_in_time=cit)
        result, _ = AttendanceService.mark_attendance(db, payload, actor.id)
        assert result.check_in_time == cit

    def test_new_record_writes_audit_log(self, db):
        """mark_attendance writes an ATTENDANCE_CREATED audit log."""
        emp = make_employee(db)
        actor = make_user(db)
        payload = make_payload(emp.id)
        result, _ = AttendanceService.mark_attendance(db, payload, actor.id)
        log = db.query(AuditLog).filter(
            AuditLog.entity_id == result.id,
            AuditLog.action == "ATTENDANCE_CREATED",
        ).first()
        assert log is not None
        assert log.actor_id == actor.id

    def test_on_leave_override_returns_200_flag(self, db):
        """Overriding an ON_LEAVE record → (Attendance, True) — caller returns 200."""
        emp = make_employee(db)
        actor = make_user(db)
        att = Attendance(
            id=uuid.uuid4(), employee_id=emp.id,
            date=date.today() - timedelta(days=2),
            status=AttendanceStatus.ON_LEAVE,
        )
        db.add(att); db.flush()
        payload = make_payload(emp.id, date_=date.today() - timedelta(days=2))
        result, was_update = AttendanceService.mark_attendance(db, payload, actor.id)
        assert was_update is True
        assert result.status == AttendanceStatus.PRESENT

    def test_duplicate_non_leave_raises_409(self, db):
        """Duplicate PRESENT/ABSENT/etc. on same date → HTTP 409."""
        emp = make_employee(db)
        actor = make_user(db)
        payload = make_payload(emp.id, date_=date.today() - timedelta(days=3))
        AttendanceService.mark_attendance(db, payload, actor.id)
        with pytest.raises(HTTPException) as exc_info:
            AttendanceService.mark_attendance(db, payload, actor.id)
        assert exc_info.value.status_code == 409

    def test_future_date_raises_400(self, db):
        """Attendance for a future date → HTTP 400."""
        emp = make_employee(db)
        actor = make_user(db)
        payload = make_payload(emp.id, date_=date.today() + timedelta(days=1))
        with pytest.raises(HTTPException) as exc_info:
            AttendanceService.mark_attendance(db, payload, actor.id)
        assert exc_info.value.status_code == 400

    def test_unknown_employee_raises_404(self, db):
        """Non-existent employee_id → HTTP 404."""
        actor = make_user(db)
        payload = make_payload(uuid.uuid4())
        with pytest.raises(HTTPException) as exc_info:
            AttendanceService.mark_attendance(db, payload, actor.id)
        assert exc_info.value.status_code == 404


# ── Task 25.3: override_attendance ───────────────────────────────────────────

class TestOverrideAttendance:

    def _make_attendance(self, db, emp_id, status=AttendanceStatus.PRESENT, d=None):
        att = Attendance(
            id=uuid.uuid4(), employee_id=emp_id,
            date=d or date.today() - timedelta(days=5),
            status=status,
        )
        db.add(att); db.flush(); return att

    def test_override_sets_all_fields(self, db):
        """override_attendance sets is_override, reason, overridden_by, overridden_at."""
        emp = make_employee(db)
        actor = make_user(db)
        att = self._make_attendance(db, emp.id)
        result = AttendanceService.override_attendance(
            db=db, attendance_id=att.id,
            new_status=AttendanceStatus.ABSENT,
            reason="Correcting error",
            overriding_user_id=actor.id,
        )
        assert result.status == AttendanceStatus.ABSENT
        assert result.is_override is True
        assert result.override_reason == "Correcting error"
        assert result.overridden_by == actor.id
        assert result.overridden_at is not None

    def test_override_writes_audit_log(self, db):
        """override_attendance writes an ATTENDANCE_OVERRIDDEN audit log."""
        emp = make_employee(db)
        actor = make_user(db)
        att = self._make_attendance(db, emp.id, d=date.today() - timedelta(days=6))
        AttendanceService.override_attendance(
            db=db, attendance_id=att.id,
            new_status=AttendanceStatus.HALF_DAY,
            reason="Test",
            overriding_user_id=actor.id,
        )
        log = db.query(AuditLog).filter(
            AuditLog.entity_id == att.id,
            AuditLog.action == "ATTENDANCE_OVERRIDDEN",
        ).first()
        assert log is not None

    def test_override_on_leave_status_via_schema_raises_422(self):
        """AttendanceOverrideRequest rejects ON_LEAVE via Pydantic validator → 422."""
        from app.schemas.attendance import AttendanceOverrideRequest, AttendanceStatus as SchemaStatus
        with pytest.raises(Exception):
            AttendanceOverrideRequest(
                status=SchemaStatus.ON_LEAVE,
                reason="test",
            )

    def test_override_missing_record_raises_404(self, db):
        """Overriding a non-existent attendance id → HTTP 404."""
        actor = make_user(db)
        with pytest.raises(HTTPException) as exc_info:
            AttendanceService.override_attendance(
                db=db, attendance_id=uuid.uuid4(),
                new_status=AttendanceStatus.PRESENT,
                reason="Test",
                overriding_user_id=actor.id,
            )
        assert exc_info.value.status_code == 404

    def test_override_can_change_any_status(self, db):
        """Override can set PRESENT, ABSENT, HALF_DAY, or LATE — all valid."""
        emp = make_employee(db)
        actor = make_user(db)
        for i, new_status in enumerate([
            AttendanceStatus.ABSENT,
            AttendanceStatus.HALF_DAY,
            AttendanceStatus.LATE,
            AttendanceStatus.PRESENT,
        ]):
            att = self._make_attendance(db, emp.id, d=date.today() - timedelta(days=10 + i))
            result = AttendanceService.override_attendance(
                db=db, attendance_id=att.id,
                new_status=new_status,
                reason="test",
                overriding_user_id=actor.id,
            )
            assert result.status == new_status
            assert result.is_override is True
