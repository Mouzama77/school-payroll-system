from datetime import date, datetime, time, timezone
from math import floor
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import extract
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.attendance import Attendance, AttendanceStatus
from app.models.employee import Employee
from app.schemas.attendance import AttendanceCreate, MonthlyAttendanceResponse
from app.models.audit_log import AuditLog


class AttendanceService:
    # ----------------------------
    # Helpers
    # ----------------------------

    @staticmethod
    def _to_date(value: date | datetime) -> date:
        if isinstance(value, datetime):
            return value.date()
        return value

    @staticmethod
    def compute_late_minutes(check_in: time, reporting_time: time) -> int:
        """Req 12.2: late_minutes = max(0, floor((check_in - reporting_time) in minutes)).
        Returns 0 if check_in <= reporting_time."""
        # Convert both times to total seconds from midnight for arithmetic
        check_in_secs = check_in.hour * 3600 + check_in.minute * 60 + check_in.second
        report_secs = reporting_time.hour * 3600 + reporting_time.minute * 60 + reporting_time.second
        diff_secs = check_in_secs - report_secs
        return max(0, floor(diff_secs / 60))

    # ----------------------------
    # Validations (READ ONLY)
    # ----------------------------

    @staticmethod
    def validate_employee_exists(db: Session, employee_id: UUID) -> Employee:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )
        return employee

    @staticmethod
    def validate_date_not_future(attendance_date: date | datetime) -> date:
        attendance_date = AttendanceService._to_date(attendance_date)

        if attendance_date > date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attendance date cannot be in the future",
            )

        return attendance_date

    @staticmethod
    def get_existing_attendance(
        db: Session,
        employee_id: UUID,
        attendance_date: date,
    ) -> Attendance | None:
        return (
            db.query(Attendance)
            .filter(
                Attendance.employee_id == employee_id,
                Attendance.date == attendance_date,
            )
            .first()
        )

    # ----------------------------
    # Core Logic
    # ----------------------------

    @staticmethod
    def mark_attendance(
        db: Session,
        payload: AttendanceCreate,
        actor_id: UUID,
    ) -> tuple[Attendance, bool]:
        """Returns (attendance, was_update).
        was_update=True when an existing ON_LEAVE record was converted (HTTP 200).
        was_update=False for new records (HTTP 201)."""

        normalized_date = AttendanceService.validate_date_not_future(payload.date)

        employee = AttendanceService.validate_employee_exists(db, payload.employee_id)

        existing = AttendanceService.get_existing_attendance(
            db,
            payload.employee_id,
            normalized_date,
        )

        # ----------------------------
        # Case 1: existing record
        # ----------------------------
        if existing:
            if existing.status == AttendanceStatus.ON_LEAVE:
                # Update existing ON_LEAVE attendance
                try:
                    existing.status = AttendanceStatus(payload.status.value)
                    db.add(
                        AuditLog(
                            actor_id=actor_id,
                            action="ATTENDANCE_UPDATED",
                            entity_type="attendance",
                            entity_id=existing.id,
                            detail=f"ON_LEAVE converted to {payload.status.value}",
                        )
                    )
                    db.commit()
                    db.refresh(existing)
                    return existing, True  # was_update → caller returns HTTP 200
                except Exception as exc:
                    db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to update attendance",
                    ) from exc

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Attendance already exists for this employee on this date",
            )

        # ----------------------------
        # Case 2: new record
        # ----------------------------
        # Req 15.3: reject attendance on non-working academic calendar dates.
        # Sundays default to holidays unless the admin explicitly marks the
        # date as a WORKING_DAY (Part 3 — no need to create every Sunday).
        from app.models.academic_calendar import AcademicCalendar
        from app.core.calender_rules import resolve_day_type

        cal_entry = db.query(AcademicCalendar).filter(
            AcademicCalendar.date == normalized_date
        ).first()
        effective_type = resolve_day_type(normalized_date, cal_entry)
        if effective_type != "WORKING_DAY":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{normalized_date} is a {effective_type} and cannot have attendance marked",
            )

        # Req 16.2: persist check_in_time when provided
        check_in_time = getattr(payload, "check_in_time", None)

        attendance = Attendance(
            employee_id=payload.employee_id,
            date=normalized_date,
            status=AttendanceStatus(payload.status.value),
            check_in_time=check_in_time,
        )

        try:
            db.add(attendance)
            db.flush()  # ensures attendance.id exists

            db.add(
                AuditLog(
                    actor_id=actor_id,
                    action="ATTENDANCE_CREATED",
                    entity_type="attendance",
                    entity_id=attendance.id,
                    detail=f"Attendance created for {payload.employee_id} on {normalized_date}",
                )
            )

            db.commit()
            db.refresh(attendance)
            return attendance, False  # was_update=False → caller returns HTTP 201

        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate attendance detected",
            ) from exc

    # ----------------------------
    # Override (UNCHANGED logic, cleaned)
    # ----------------------------

    @staticmethod
    def override_attendance(
        db: Session,
        attendance_id: UUID,
        new_status: AttendanceStatus,
        reason: str,
        overriding_user_id: UUID,
    ) -> Attendance:

        attendance = db.get(Attendance, attendance_id)

        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance record not found",
            )

        attendance.status = new_status
        attendance.is_override = True
        attendance.override_reason = reason
        attendance.overridden_by = overriding_user_id
        attendance.overridden_at = datetime.now(timezone.utc)

        db.add(
            AuditLog(
                actor_id=overriding_user_id,
                action="ATTENDANCE_OVERRIDDEN",
                entity_type="attendance",
                entity_id=attendance_id,
                detail=f"Overridden to {new_status.value}: {reason}",
            )
        )

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(attendance)
        return attendance

    # ----------------------------
    # Monthly report
    # ----------------------------

    @staticmethod
    def get_monthly_attendance(
        db: Session,
        employee_id: UUID,
        month: int,
        year: int,
    ) -> MonthlyAttendanceResponse:

        AttendanceService.validate_employee_exists(db, employee_id)

        records = (
            db.query(Attendance)
            .filter(
                Attendance.employee_id == employee_id,
                extract("month", Attendance.date) == month,
                extract("year", Attendance.date) == year,
            )
            .order_by(Attendance.date.asc())
            .all()
        )

        summary = {
            "total_present": sum(r.status == AttendanceStatus.PRESENT for r in records),
            "total_absent": sum(r.status == AttendanceStatus.ABSENT for r in records),
            "total_half_days": sum(r.status == AttendanceStatus.HALF_DAY for r in records),
            "total_late_days": sum(r.status == AttendanceStatus.LATE for r in records),
        }

        return MonthlyAttendanceResponse(
            employee_id=employee_id,
            month=month,
            year=year,
            records=records,
            summary=summary,
        )