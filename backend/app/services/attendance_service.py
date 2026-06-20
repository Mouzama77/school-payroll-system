from datetime import date, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.models.attendance import Attendance, AttendanceStatus
from app.models.employee import Employee
from app.schemas.attendance import AttendanceCreate, AttendanceReportResponse


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
        attendance_id: UUID | None = None,
    ) -> None:
        query = db.query(Attendance).filter(
            Attendance.employee_id == employee_id,
            Attendance.date == attendance_date,
        )
        if attendance_id is not None:
            query = query.filter(Attendance.id != attendance_id)
        if query.first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Attendance already exists for this employee on this date",
            )

    @staticmethod
    def create(db: Session, payload: AttendanceCreate) -> Attendance:
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
        db.commit()
        db.refresh(attendance)
        return attendance

    @staticmethod
    def get_monthly_report(
        db: Session,
        employee_id: UUID,
        month: int,
        year: int,
    ) -> AttendanceReportResponse:
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
            "total_present": sum(
                1 for record in records if record.status == AttendanceStatus.PRESENT
            ),
            "total_absent": sum(
                1 for record in records if record.status == AttendanceStatus.ABSENT
            ),
            "total_half_days": sum(
                1 for record in records if record.status == AttendanceStatus.HALF_DAY
            ),
        }

        return AttendanceReportResponse(
            employee_id=employee_id,
            month=month,
            year=year,
            records=records,
            summary=summary,
        )
