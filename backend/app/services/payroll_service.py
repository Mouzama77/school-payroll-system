from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.payroll import Payroll
from app.schemas.payroll import PayrollResponse
from app.services.attendance_service import AttendanceService

WORKING_DAYS = 30


class PayrollService:
    @staticmethod
    def _month_key(month: int, year: int) -> str:
        return f"{year:04d}-{month:02d}"

    @staticmethod
    def _parse_month_key(month_key: str) -> tuple[int, int]:
        year_str, month_str = month_key.split("-")
        return int(month_str), int(year_str)

    @staticmethod
    def _round_money(amount: float) -> float:
        return round(amount, 2)

    @staticmethod
    def _calculate_amounts(
        base_salary: float,
        total_present: int,
        total_absent: int,
        total_half_days: int,
    ) -> dict[str, float | int]:
        daily_salary = base_salary / WORKING_DAYS
        absent_deductions = total_absent * daily_salary
        half_day_deductions = total_half_days * daily_salary * 0.5
        total_deductions = absent_deductions + half_day_deductions
        net_salary = base_salary - total_deductions

        return {
            "total_present": total_present,
            "total_absent": total_absent,
            "total_half_days": total_half_days,
            "daily_salary": PayrollService._round_money(daily_salary),
            "absent_deductions": PayrollService._round_money(absent_deductions),
            "half_day_deductions": PayrollService._round_money(half_day_deductions),
            "total_deductions": PayrollService._round_money(total_deductions),
            "net_salary": PayrollService._round_money(net_salary),
        }

    @staticmethod
    def _to_response(payroll: Payroll) -> PayrollResponse:
        month, year = PayrollService._parse_month_key(payroll.month)
        amounts = PayrollService._calculate_amounts(
            base_salary=payroll.base_salary,
            total_present=payroll.days_present or 0,
            total_absent=payroll.total_absent,
            total_half_days=payroll.total_half_days,
        )

        return PayrollResponse(
            id=payroll.id,
            employee_id=payroll.employee_id,
            month=month,
            year=year,
            base_salary=payroll.base_salary,
            total_working_days=payroll.total_working_days or WORKING_DAYS,
            total_present=amounts["total_present"],
            total_absent=amounts["total_absent"],
            total_half_days=amounts["total_half_days"],
            daily_salary=amounts["daily_salary"],
            absent_deductions=amounts["absent_deductions"],
            half_day_deductions=amounts["half_day_deductions"],
            total_deductions=amounts["total_deductions"],
            net_salary=payroll.net_salary or amounts["net_salary"],
            status=payroll.status,
            created_at=payroll.created_at,
        )

    @staticmethod
    def _get_existing_payroll(
        db: Session,
        employee_id: UUID,
        month: int,
        year: int,
    ) -> Payroll | None:
        month_key = PayrollService._month_key(month, year)
        return (
            db.query(Payroll)
            .filter(
                Payroll.employee_id == employee_id,
                Payroll.month == month_key,
            )
            .first()
        )

    @staticmethod
    def generate_payroll(
        db: Session,
        employee_id: UUID,
        month: int,
        year: int,
    ) -> PayrollResponse:
        employee = AttendanceService.validate_employee_exists(db, employee_id)
        month_key = PayrollService._month_key(month, year)

        if PayrollService._get_existing_payroll(db, employee_id, month, year):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payroll already exists for this employee and month",
            )

        attendance = AttendanceService.get_monthly_attendance(
            db=db,
            employee_id=employee_id,
            month=month,
            year=year,
        )
        amounts = PayrollService._calculate_amounts(
            base_salary=employee.salary,
            total_present=attendance.summary.total_present,
            total_absent=attendance.summary.total_absent,
            total_half_days=attendance.summary.total_half_days,
        )

        payroll = Payroll(
            employee_id=employee_id,
            month=month_key,
            base_salary=gross,
            total_working_days=WORKING_DAYS,
            days_present=attendance.summary.total_present,
            total_absent=attendance.summary.total_absent,
            total_half_days=attendance.summary.total_half_days,
            leave_deductions=epf,
            overtime_bonus=tax,
            net_salary=net_salary,
            status="generated",
        )
        db.add(payroll)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payroll already exists for this employee and month",
            )
        db.refresh(payroll)
        return PayrollService._to_response(payroll)

    @staticmethod
    def get_payroll(
        db: Session,
        employee_id: UUID,
        month: int,
        year: int,
    ) -> PayrollResponse:
        AttendanceService.validate_employee_exists(db, employee_id)

        payroll = PayrollService._get_existing_payroll(db, employee_id, month, year)
        if not payroll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payroll not found for this employee and month",
            )
        return PayrollService._to_response(payroll)

    @staticmethod
    def recalculate_payroll(
        db: Session,
        employee_id: UUID,
        month: int,
        year: int,
    ) -> PayrollResponse:
        """Recalculate an existing payroll snapshot using current attendance data.

        This is the correct path after an attendance override: the override
        changes the attendance record in place, then this method re-reads the
        attendance summary and updates the stored payroll snapshot to match.

        Raises 404 if no payroll record exists for the given employee/month.
        Use generate_payroll to create the initial record.
        """
        employee = AttendanceService.validate_employee_exists(db, employee_id)

        payroll = PayrollService._get_existing_payroll(db, employee_id, month, year)
        if not payroll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payroll not found for this employee and month. Use generate_payroll first.",
            )

        # Re-read attendance — this reflects any overrides applied since generation.
        attendance = AttendanceService.get_monthly_attendance(
            db=db,
            employee_id=employee_id,
            month=month,
            year=year,
        )
        amounts = PayrollService._calculate_amounts(
            base_salary=employee.salary,
            total_present=attendance.summary.total_present,
            total_absent=attendance.summary.total_absent,
            total_half_days=attendance.summary.total_half_days,
        )

        # Update the stored snapshot fields in place.
        payroll.days_present = attendance.summary.total_present
        payroll.total_absent = attendance.summary.total_absent
        payroll.total_half_days = attendance.summary.total_half_days
        payroll.leave_deductions = epf
        payroll.overtime_bonus = tax
        payroll.net_salary = net_salary
        payroll.status = "recalculated"

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(payroll)
        return PayrollService._to_response(payroll)
