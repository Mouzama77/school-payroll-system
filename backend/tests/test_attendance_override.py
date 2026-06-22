"""
Tests for the attendance override feature.

Covers:
- AttendanceOverrideRequest schema validation
- AttendanceService.override_attendance() service logic (using an in-memory
  SQLite database so no real PostgreSQL connection is needed)
"""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.models.attendance import Attendance, AttendanceStatus
from app.schemas.attendance import AttendanceOverrideRequest


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestAttendanceOverrideRequestSchema:
    def test_valid_payload(self):
        req = AttendanceOverrideRequest(status="PRESENT", reason="Employee attended training")
        assert req.status == AttendanceStatus.PRESENT
        assert req.reason == "Employee attended training"

    def test_reason_is_stripped(self):
        req = AttendanceOverrideRequest(status="LATE", reason="  late arrival  ")
        assert req.reason == "late arrival"

    def test_all_valid_override_statuses_accepted(self):
        for status_val in ("PRESENT", "ABSENT", "HALF_DAY", "LATE"):
            req = AttendanceOverrideRequest(status=status_val, reason="Valid reason")
            assert req.status.value == status_val

    def test_on_leave_status_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            AttendanceOverrideRequest(status="ON_LEAVE", reason="Some reason")
        errors = exc_info.value.errors()
        assert any("ON_LEAVE" in str(e) for e in errors)

    def test_blank_reason_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            AttendanceOverrideRequest(status="PRESENT", reason="   ")
        errors = exc_info.value.errors()
        assert any("reason" in str(e).lower() for e in errors)

    def test_empty_reason_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            AttendanceOverrideRequest(status="PRESENT", reason="")
        errors = exc_info.value.errors()
        assert any("reason" in str(e).lower() for e in errors)

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            AttendanceOverrideRequest(status="UNKNOWN_STATUS", reason="Some reason")


# ---------------------------------------------------------------------------
# Service logic tests (mocked DB session)
# ---------------------------------------------------------------------------


def _make_attendance(status: AttendanceStatus = AttendanceStatus.ON_LEAVE) -> Attendance:
    """Return a minimal Attendance ORM object with required fields populated."""
    record = Attendance(
        employee_id=uuid.uuid4(),
        date=date.today(),
        status=status,
    )
    record.id = uuid.uuid4()
    record.is_override = False
    record.override_reason = None
    record.overridden_by = None
    record.overridden_at = None
    return record


class TestAttendanceServiceOverride:
    def _make_db(self, attendance: Attendance | None):
        """Build a mock SQLAlchemy Session that returns the given attendance record."""
        db = MagicMock()
        db.get.return_value = attendance
        db.commit = MagicMock()
        db.rollback = MagicMock()
        db.refresh = MagicMock()
        return db

    def test_override_on_leave_to_present(self):
        from app.services.attendance_service import AttendanceService

        record = _make_attendance(AttendanceStatus.ON_LEAVE)
        db = self._make_db(record)
        overriding_user_id = uuid.uuid4()

        result = AttendanceService.override_attendance(
            db=db,
            attendance_id=record.id,
            new_status=AttendanceStatus.PRESENT,
            reason="Employee attended training",
            overriding_user_id=overriding_user_id,
        )

        assert result.status == AttendanceStatus.PRESENT
        assert result.is_override is True
        assert result.override_reason == "Employee attended training"
        assert result.overridden_by == overriding_user_id
        assert result.overridden_at is not None
        db.commit.assert_called_once()
        db.rollback.assert_not_called()

    def test_override_sets_overridden_at_as_utc(self):
        from app.services.attendance_service import AttendanceService

        record = _make_attendance(AttendanceStatus.ON_LEAVE)
        db = self._make_db(record)
        before = datetime.now(timezone.utc)

        AttendanceService.override_attendance(
            db=db,
            attendance_id=record.id,
            new_status=AttendanceStatus.ABSENT,
            reason="No show",
            overriding_user_id=uuid.uuid4(),
        )

        after = datetime.now(timezone.utc)
        assert before <= record.overridden_at <= after

    def test_override_any_existing_status(self):
        """Any status — not just ON_LEAVE — can be overridden."""
        from app.services.attendance_service import AttendanceService

        for initial_status in (
            AttendanceStatus.PRESENT,
            AttendanceStatus.ABSENT,
            AttendanceStatus.HALF_DAY,
            AttendanceStatus.LATE,
            AttendanceStatus.ON_LEAVE,
        ):
            record = _make_attendance(initial_status)
            db = self._make_db(record)

            result = AttendanceService.override_attendance(
                db=db,
                attendance_id=record.id,
                new_status=AttendanceStatus.PRESENT,
                reason="Override test",
                overriding_user_id=uuid.uuid4(),
            )
            assert result.is_override is True

    def test_override_raises_404_when_not_found(self):
        from fastapi import HTTPException

        from app.services.attendance_service import AttendanceService

        db = self._make_db(None)  # record not found

        with pytest.raises(HTTPException) as exc_info:
            AttendanceService.override_attendance(
                db=db,
                attendance_id=uuid.uuid4(),
                new_status=AttendanceStatus.PRESENT,
                reason="Test",
                overriding_user_id=uuid.uuid4(),
            )
        assert exc_info.value.status_code == 404

    def test_rollback_called_on_commit_failure(self):
        from app.services.attendance_service import AttendanceService

        record = _make_attendance(AttendanceStatus.ON_LEAVE)
        db = self._make_db(record)
        db.commit.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            AttendanceService.override_attendance(
                db=db,
                attendance_id=record.id,
                new_status=AttendanceStatus.PRESENT,
                reason="Test rollback",
                overriding_user_id=uuid.uuid4(),
            )

        db.rollback.assert_called_once()

    def test_override_audit_fields_stored(self):
        """Verify all four audit fields are written in one call."""
        from app.services.attendance_service import AttendanceService

        record = _make_attendance(AttendanceStatus.ON_LEAVE)
        db = self._make_db(record)
        user_id = uuid.uuid4()

        AttendanceService.override_attendance(
            db=db,
            attendance_id=record.id,
            new_status=AttendanceStatus.LATE,
            reason="Came in late",
            overriding_user_id=user_id,
        )

        assert record.is_override is True
        assert record.override_reason == "Came in late"
        assert record.overridden_by == user_id
        assert isinstance(record.overridden_at, datetime)


# ---------------------------------------------------------------------------
# Payroll summary — ON_LEAVE days must not affect deductions
# ---------------------------------------------------------------------------


class TestPayrollSummaryExcludesOnLeave:
    def test_on_leave_not_counted_in_summary(self):
        """Monthly attendance summary must exclude ON_LEAVE from all counters."""
        from app.services.attendance_service import AttendanceService

        employee_id = uuid.uuid4()
        records = [
            Attendance(employee_id=employee_id, date=date(2026, 6, 1), status=AttendanceStatus.PRESENT),
            Attendance(employee_id=employee_id, date=date(2026, 6, 2), status=AttendanceStatus.ON_LEAVE),
            Attendance(employee_id=employee_id, date=date(2026, 6, 3), status=AttendanceStatus.ABSENT),
            Attendance(employee_id=employee_id, date=date(2026, 6, 4), status=AttendanceStatus.HALF_DAY),
            Attendance(employee_id=employee_id, date=date(2026, 6, 5), status=AttendanceStatus.LATE),
        ]

        # Patch the DB query so we don't need a real DB
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = records

        with patch.object(AttendanceService, "validate_employee_exists", return_value=MagicMock()):
            response = AttendanceService.get_monthly_attendance(
                db=db,
                employee_id=employee_id,
                month=6,
                year=2026,
            )

        assert response.summary.total_present == 1
        assert response.summary.total_absent == 1
        assert response.summary.total_half_days == 1
        # ON_LEAVE and LATE are intentionally excluded from the three counters
