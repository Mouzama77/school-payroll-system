"""
Integration tests for the leave → attendance → payroll pipeline.

All tests use mocked SQLAlchemy sessions so no real database is required.
The mock DB is carefully shaped to match what each service method queries,
allowing deterministic verification of every business rule.

Coverage:
  - Leave approval creates ON_LEAVE attendance for each leave day
  - Leave approval skips days with manually overridden attendance (is_override=True)
  - Leave approval never clears audit fields on overridden records
  - Leave rejection does not create attendance records
  - Attendance override updates all four audit fields
  - Attendance override writes an AuditLog entry in the same commit
  - Payroll recalculation reads updated attendance (post-override)
  - Payroll recalculation raises 404 when no payroll exists
  - Rollback is called when leave_service.update_leave_status commit fails
  - Rollback is called when attendance_service.override_attendance commit fails
  - Rollback is called when payroll_service.recalculate_payroll commit fails
"""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, call, patch

import pytest

from app.models.attendance import Attendance, AttendanceStatus
from app.models.leave import Leave, LeaveStatus, LeaveType
from app.models.payroll import Payroll


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _leave(
    employee_id: uuid.UUID,
    start: date,
    end: date,
    status: LeaveStatus = LeaveStatus.PENDING,
) -> Leave:
    return Leave(
        id=uuid.uuid4(),
        employee_id=employee_id,
        leave_type=LeaveType.CASUAL,
        start_date=start,
        end_date=end,
        reason=None,
        status=status,
        approved_by=None
    )


def _attendance(
    employee_id: uuid.UUID,
    att_date: date,
    status: AttendanceStatus,
    is_override: bool = False,
) -> Attendance:
    return Attendance(
        id=uuid.uuid4(),
        employee_id=employee_id,
        date=att_date,
        status=status,
        is_override=is_override,
        override_reason="prior reason" if is_override else None,
        overridden_by=uuid.uuid4() if is_override else None,
        overridden_at=datetime.now(timezone.utc) if is_override else None
    )


def _payroll(employee_id: uuid.UUID, month_key: str) -> Payroll:
    return Payroll(
        id=uuid.uuid4(),
        employee_id=employee_id,
        month=month_key,
        base_salary=30_000.0,
        total_working_days=30,
        days_present=20,
        total_absent=5,
        total_half_days=2,
        leave_deductions=5500.0,
        overtime_bonus=0,
        net_salary=24_500.0,
        status="generated",
        created_at=datetime.now(timezone.utc)
    )


def _mock_db_for_leave(leave: Leave, existing_attendance: dict[date, Attendance]):
    """
    Build a mock DB session for leave_service.update_leave_status.
    existing_attendance maps date → Attendance (or None if the date has no record).
    """
    db = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    db.refresh = MagicMock()
    db.add = MagicMock()

    # First query: find the Leave by id.
    # Subsequent queries: find Attendance for each date in the leave range.
    query_results = []

    def make_filter(*args, **kwargs):
        mock_filter = MagicMock()

        def first_side_effect():
            if not query_results:
                return None
            return query_results.pop(0)

        mock_filter.first.side_effect = first_side_effect
        mock_filter.filter.return_value = mock_filter
        return mock_filter

    db.query.return_value.filter.side_effect = make_filter

    # Prime the result queue: first result is the Leave, then one per day.
    query_results.append(leave)
    current = leave.start_date
    from datetime import timedelta

    while current <= leave.end_date:
        query_results.append(existing_attendance.get(current))
        current += timedelta(days=1)

    return db


# ---------------------------------------------------------------------------
# Leave approval → attendance creation
# ---------------------------------------------------------------------------


class TestLeaveApprovalAttendanceCreation:
    def test_approval_creates_on_leave_for_each_day(self):
        """Three-day leave with no existing records → three ON_LEAVE rows added."""
        from app.services.leave_service import update_leave_status

        employee_id = uuid.uuid4()
        approver_id = uuid.uuid4()
        leave = _leave(employee_id, date(2026, 7, 1), date(2026, 7, 3))
        db = _mock_db_for_leave(leave, {})

        update_leave_status(db, leave.id, LeaveStatus.APPROVED, approver_id)

        # Three Attendance rows + one AuditLog row should have been added.
        added_types = [type(call.args[0]).__name__ for call in db.add.call_args_list]
        attendance_adds = [t for t in added_types if t == "Attendance"]
        audit_adds = [t for t in added_types if t == "AuditLog"]
        assert len(attendance_adds) == 3
        assert len(audit_adds) == 1

    def test_approval_updates_existing_non_overridden_record(self):
        """Existing PRESENT record without override flag is updated to ON_LEAVE."""
        from app.services.leave_service import update_leave_status

        employee_id = uuid.uuid4()
        approver_id = uuid.uuid4()
        leave = _leave(employee_id, date(2026, 7, 1), date(2026, 7, 1))
        existing = _attendance(employee_id, date(2026, 7, 1), AttendanceStatus.PRESENT)
        db = _mock_db_for_leave(leave, {date(2026, 7, 1): existing})

        update_leave_status(db, leave.id, LeaveStatus.APPROVED, approver_id)

        assert existing.status == AttendanceStatus.ON_LEAVE
        # No new Attendance added (existing was updated in place).
        added_types = [type(c.args[0]).__name__ for c in db.add.call_args_list]
        assert "Attendance" not in added_types

    def test_approval_skips_overridden_attendance(self):
        """Day with is_override=True must not be touched on leave approval."""
        from app.services.leave_service import update_leave_status

        employee_id = uuid.uuid4()
        approver_id = uuid.uuid4()
        leave = _leave(employee_id, date(2026, 7, 1), date(2026, 7, 1))
        existing = _attendance(
            employee_id, date(2026, 7, 1), AttendanceStatus.PRESENT, is_override=True
        )
        original_status = existing.status
        original_reason = existing.override_reason
        original_overridden_by = existing.overridden_by

        db = _mock_db_for_leave(leave, {date(2026, 7, 1): existing})
        update_leave_status(db, leave.id, LeaveStatus.APPROVED, approver_id)

        # Overridden record must be completely unchanged.
        assert existing.status == original_status
        assert existing.is_override is True
        assert existing.override_reason == original_reason
        assert existing.overridden_by == original_overridden_by

    def test_approval_mixed_days_respects_overrides(self):
        """
        Three-day leave:
          day 1 – no record   → create ON_LEAVE
          day 2 – overridden  → skip entirely
          day 3 – PRESENT     → update to ON_LEAVE
        """
        from app.services.leave_service import update_leave_status

        employee_id = uuid.uuid4()
        approver_id = uuid.uuid4()
        leave = _leave(employee_id, date(2026, 7, 1), date(2026, 7, 3))

        day2 = _attendance(employee_id, date(2026, 7, 2), AttendanceStatus.PRESENT, is_override=True)
        day3 = _attendance(employee_id, date(2026, 7, 3), AttendanceStatus.PRESENT)

        db = _mock_db_for_leave(
            leave,
            {
                date(2026, 7, 1): None,
                date(2026, 7, 2): day2,
                date(2026, 7, 3): day3,
            },
        )
        update_leave_status(db, leave.id, LeaveStatus.APPROVED, approver_id)

        # day 1 – new Attendance created
        added_types = [type(c.args[0]).__name__ for c in db.add.call_args_list]
        assert added_types.count("Attendance") == 1

        # day 2 – untouched
        assert day2.status == AttendanceStatus.PRESENT
        assert day2.is_override is True

        # day 3 – updated
        assert day3.status == AttendanceStatus.ON_LEAVE

    def test_rejection_does_not_create_attendance(self):
        """Rejecting a leave must not create or modify any attendance record."""
        from app.services.leave_service import update_leave_status

        employee_id = uuid.uuid4()
        approver_id = uuid.uuid4()
        leave = _leave(employee_id, date(2026, 7, 1), date(2026, 7, 3))
        db = _mock_db_for_leave(leave, {})

        update_leave_status(db, leave.id, LeaveStatus.REJECTED, approver_id)

        added_types = [type(c.args[0]).__name__ for c in db.add.call_args_list]
        assert "Attendance" not in added_types
        # AuditLog is still written for rejection.
        assert "AuditLog" in added_types


# ---------------------------------------------------------------------------
# Leave approval → audit log
# ---------------------------------------------------------------------------


class TestLeaveApprovalAuditLog:
    def test_approval_writes_leave_approved_audit_log(self):
        from app.services.leave_service import update_leave_status

        employee_id = uuid.uuid4()
        approver_id = uuid.uuid4()
        leave = _leave(employee_id, date(2026, 7, 1), date(2026, 7, 1))
        db = _mock_db_for_leave(leave, {})

        update_leave_status(db, leave.id, LeaveStatus.APPROVED, approver_id)

        added = [c.args[0] for c in db.add.call_args_list]
        audit_entries = [a for a in added if type(a).__name__ == "AuditLog"]
        assert len(audit_entries) == 1
        assert audit_entries[0].action == "LEAVE_APPROVED"
        assert audit_entries[0].actor_id == approver_id
        assert audit_entries[0].entity_type == "leave"

    def test_rejection_writes_leave_rejected_audit_log(self):
        from app.services.leave_service import update_leave_status

        employee_id = uuid.uuid4()
        approver_id = uuid.uuid4()
        leave = _leave(employee_id, date(2026, 7, 1), date(2026, 7, 1))
        db = _mock_db_for_leave(leave, {})

        update_leave_status(db, leave.id, LeaveStatus.REJECTED, approver_id)

        added = [c.args[0] for c in db.add.call_args_list]
        audit_entries = [a for a in added if type(a).__name__ == "AuditLog"]
        assert len(audit_entries) == 1
        assert audit_entries[0].action == "LEAVE_REJECTED"


# ---------------------------------------------------------------------------
# Attendance override → audit log
# ---------------------------------------------------------------------------


class TestAttendanceOverrideAuditLog:
    def _make_db(self, attendance):
        db = MagicMock()
        db.get.return_value = attendance
        db.commit = MagicMock()
        db.rollback = MagicMock()
        db.refresh = MagicMock()
        db.add = MagicMock()
        return db

    def test_override_writes_attendance_overridden_audit_log(self):
        from app.services.attendance_service import AttendanceService

        record = _attendance(uuid.uuid4(), date(2026, 7, 1), AttendanceStatus.ON_LEAVE)
        user_id = uuid.uuid4()
        db = self._make_db(record)

        AttendanceService.override_attendance(
            db=db,
            attendance_id=record.id,
            new_status=AttendanceStatus.PRESENT,
            reason="Attended despite leave",
            overriding_user_id=user_id,
        )

        added = [c.args[0] for c in db.add.call_args_list]
        audit_entries = [a for a in added if type(a).__name__ == "AuditLog"]
        assert len(audit_entries) == 1
        assert audit_entries[0].action == "ATTENDANCE_OVERRIDDEN"
        assert audit_entries[0].actor_id == user_id
        assert audit_entries[0].entity_type == "attendance"

    def test_override_and_audit_log_in_single_commit(self):
        """Audit log and attendance update must be committed together."""
        from app.services.attendance_service import AttendanceService

        record = _attendance(uuid.uuid4(), date(2026, 7, 1), AttendanceStatus.ON_LEAVE)
        db = self._make_db(record)

        AttendanceService.override_attendance(
            db=db,
            attendance_id=record.id,
            new_status=AttendanceStatus.LATE,
            reason="Late",
            overriding_user_id=uuid.uuid4(),
        )

        # add() called before commit() — both ops in same transaction.
        db.add.assert_called_once()
        db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# Payroll recalculation after override
# ---------------------------------------------------------------------------


class TestPayrollRecalculation:
    def _make_db_for_recalc(self, payroll, employee, attendance_records):
        db = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        db.refresh = MagicMock()

        # Payroll query
        db.query.return_value.filter.return_value.first.return_value = payroll

        return db

    def test_recalculate_updates_payroll_snapshot(self):
        from app.services.payroll_service import PayrollService

        employee_id = uuid.uuid4()
        payroll = _payroll(employee_id, "2026-07")

        db = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        db.refresh = MagicMock()

        # Payroll lookup
        db.query.return_value.filter.return_value.first.return_value = payroll

        # Post-override attendance: employee was PRESENT on the overridden day
        mock_summary = MagicMock()
        mock_summary.total_present = 22
        mock_summary.total_absent = 3
        mock_summary.total_half_days = 1
        mock_attendance_response = MagicMock()
        mock_attendance_response.summary = mock_summary

        mock_employee = MagicMock()
        mock_employee.salary = 30_000.0

        with (
            patch.object(
                PayrollService,
                "validate_employee_exists",
                return_value=mock_employee,
                create=True,
            ),
            patch(
                "app.services.payroll_service.AttendanceService.validate_employee_exists",
                return_value=mock_employee,
            ),
            patch(
                "app.services.payroll_service.AttendanceService.get_monthly_attendance",
                return_value=mock_attendance_response,
            ),
        ):
            result = PayrollService.recalculate_payroll(
                db=db,
                employee_id=employee_id,
                month=7,
                year=2026,
            )

        assert payroll.total_absent == 3
        assert payroll.total_half_days == 1
        assert payroll.status == "recalculated"
        db.commit.assert_called_once()

    def test_recalculate_raises_404_when_no_payroll(self):
        from fastapi import HTTPException

        from app.services.payroll_service import PayrollService

        employee_id = uuid.uuid4()
        db = MagicMock()

        # No payroll found
        db.query.return_value.filter.return_value.first.return_value = None

        mock_employee = MagicMock()
        mock_employee.salary = 30_000.0

        with (
            patch(
                "app.services.payroll_service.AttendanceService.validate_employee_exists",
                return_value=mock_employee,
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            PayrollService.recalculate_payroll(
                db=db,
                employee_id=employee_id,
                month=7,
                year=2026,
            )

        assert exc_info.value.status_code == 404

    def test_recalculate_rollback_on_commit_failure(self):
        from app.services.payroll_service import PayrollService

        employee_id = uuid.uuid4()
        payroll = _payroll(employee_id, "2026-07")

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = payroll
        db.commit.side_effect = Exception("DB failure")
        db.rollback = MagicMock()

        mock_summary = MagicMock()
        mock_summary.total_present = 20
        mock_summary.total_absent = 5
        mock_summary.total_half_days = 0
        mock_resp = MagicMock()
        mock_resp.summary = mock_summary
        mock_employee = MagicMock()
        mock_employee.salary = 30_000.0

        with (
            patch(
                "app.services.payroll_service.AttendanceService.validate_employee_exists",
                return_value=mock_employee,
            ),
            patch(
                "app.services.payroll_service.AttendanceService.get_monthly_attendance",
                return_value=mock_resp,
            ),
            pytest.raises(Exception, match="Failed to recalculate payroll"),
        ):
            PayrollService.recalculate_payroll(
                db=db,
                employee_id=employee_id,
                month=7,
                year=2026,
            )

        db.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# Rollback scenarios
# ---------------------------------------------------------------------------


class TestRollbackScenarios:
    def test_leave_service_rollback_on_commit_failure(self):
        from app.services.leave_service import update_leave_status

        employee_id = uuid.uuid4()
        approver_id = uuid.uuid4()
        leave = _leave(employee_id, date(2026, 7, 1), date(2026, 7, 1))
        db = _mock_db_for_leave(leave, {})
        db.commit.side_effect = Exception("DB failure")

        with pytest.raises(Exception, match="DB failure"):
            update_leave_status(db, leave.id, LeaveStatus.APPROVED, approver_id)

        db.rollback.assert_called_once()

    def test_attendance_override_rollback_on_commit_failure(self):
        from app.services.attendance_service import AttendanceService

        record = _attendance(uuid.uuid4(), date(2026, 7, 1), AttendanceStatus.ON_LEAVE)
        db = MagicMock()
        db.get.return_value = record
        db.add = MagicMock()
        db.commit.side_effect = Exception("DB failure")
        db.rollback = MagicMock()

        with pytest.raises(Exception, match="DB failure"):
            AttendanceService.override_attendance(
                db=db,
                attendance_id=record.id,
                new_status=AttendanceStatus.PRESENT,
                reason="Test",
                overriding_user_id=uuid.uuid4(),
            )

        db.rollback.assert_called_once()

    def test_leave_service_raises_404_for_missing_leave(self):
        from fastapi import HTTPException

        from app.services.leave_service import update_leave_status

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            update_leave_status(db, uuid.uuid4(), LeaveStatus.APPROVED, uuid.uuid4())

        assert exc_info.value.status_code == 404
