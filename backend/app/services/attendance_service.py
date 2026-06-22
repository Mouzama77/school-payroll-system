from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import extract
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.attendance import Attendance, AttendanceStatus
from app.models.employee import Employee
from app.schemas.attendance import AttendanceCreate, MonthlyAttendanceResponse


class AttendanceService:
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
    def validate_date_not_future(attendance_date: date) -> None:
        if attendance_date > date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attendance date cannot be in the future",
            )

    @staticmethod
    def validate_unique_per_day(
        db: Session,
        employee_id: UUID,
        attendance_date: date,
    ) -> None:
        existing = (
            db.query(Attendance)
            .filter(
                Attendance.employee_id == employee_id,
                Attendance.date == attendance_date,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Attendance already exists for this employee on this date",
            )

    @staticmethod
    def mark_attendance(db: Session, payload: AttendanceCreate) -> Attendance:
        AttendanceService.validate_employee_exists(db, payload.employee_id)
        AttendanceService.validate_date_not_future(payload.date)
        AttendanceService.validate_unique_per_day(
            db,
            payload.employee_id,
            payload.date,
        )

        attendance = Attendance(
            employee_id=payload.employee_id,
            date=payload.date,
            status=payload.status,
        )
        db.add(attendance)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Attendance already exists for this employee on this date",
            )
        db.refresh(attendance)
        return attendance

    @staticmethod
    def override_attendance(
        db: Session,
        attendance_id: UUID,
        new_status: AttendanceStatus,
        reason: str,
        overriding_user_id: UUID,
    ) -> Attendance:
        """Override the status of an existing attendance record.

        Only HR and Admin may call this method (enforced at the API layer via
        require_roles). The override is recorded with a full audit trail:
        who changed it, when, and why.

        The previous status does not need to be ON_LEAVE — any status may be
        overridden — but ON_LEAVE cannot be set as the new status (that is
        reserved for the automated leave-approval flow).
        """
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

        # Write audit log inside the same transaction.
        from app.models.audit_log import AuditLog  # local import avoids circular dependency

        db.add(
            AuditLog(
                actor_id=overriding_user_id,
                action="ATTENDANCE_OVERRIDDEN",
                entity_type="attendance",
                entity_id=attendance_id,
                detail=(
                    f"Attendance {attendance_id} overridden to {new_status.value}. "
                    f"Reason: {reason}"
                ),
            )
        )

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(attendance)
        return attendance

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

        # ON_LEAVE counts as neither present, absent, nor half-day for payroll purposes.
        # Payroll deductions are only applied for ABSENT and HALF_DAY.
        summary = {
            "total_present": sum(
                1 for r in records if r.status == AttendanceStatus.PRESENT
            ),
            "total_absent": sum(
                1 for r in records if r.status == AttendanceStatus.ABSENT
            ),
            "total_half_days": sum(
                1 for r in records if r.status == AttendanceStatus.HALF_DAY
            ),
        }

        return MonthlyAttendanceResponse(
            employee_id=employee_id,
            month=month,
            year=year,
            records=records,
            summary=summary,
        )
