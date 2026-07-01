from __future__ import annotations

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.payroll import Payroll
from app.schemas.payroll import PayrollResponse
from app.services.attendance_service import AttendanceService

logger = logging.getLogger(__name__)

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
    def _normalize_attendance_summary(summary) -> dict[str, int]:
        """Normalize attendance.summary into the required dict format.

        Expected format everywhere:
        {
          "total_present": int,
          "total_absent": int,
          "total_half_days": int
        }
        """

        default_summary = {
            "total_present": 0,
            "total_absent": 0,
            "total_half_days": 0,
        }

        if summary is None:
            return default_summary

        # Dict-like
        if isinstance(summary, dict):
            return {
                "total_present": int(summary.get("total_present", 0) or 0),
                "total_absent": int(summary.get("total_absent", 0) or 0),
                "total_half_days": int(summary.get("total_half_days", 0) or 0),
            }

        # Object-like fallback
        get_attr = lambda name: getattr(summary, name, 0)  # noqa: E731
        return {
            "total_present": int(get_attr("total_present") or 0),
            "total_absent": int(get_attr("total_absent") or 0),
            "total_half_days": int(get_attr("total_half_days") or 0),
        }

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
            leave_deductions=PayrollService._round_money(payroll.leave_deductions or 0),
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
        """Generate a payroll snapshot for an employee and month.

        Production hardening fixes:
        - validate employee before payroll execution
        - normalize attendance.summary
        - safe null handling
        - debug logging for payroll flow
        """

        logger.debug(
            "generate_payroll start employee_id=%s month=%s year=%s",
            employee_id,
            month,
            year,
        )

        try:
            employee = AttendanceService.validate_employee_exists(db, employee_id)
        except HTTPException:
            logger.debug("generate_payroll employee validation failed employee_id=%s", employee_id)
            raise

        base_salary = getattr(employee, "salary", None)
        if base_salary is None or base_salary <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Base salary must be a positive value",
            )

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

        summary = PayrollService._normalize_attendance_summary(getattr(attendance, "summary", None))
        logger.debug(
            "generate_payroll attendance summary employee_id=%s summary=%s",
            employee_id,
            summary,
        )

        amounts = PayrollService._calculate_amounts(
            base_salary=base_salary,
            total_present=summary["total_present"],
            total_absent=summary["total_absent"],
            total_half_days=summary["total_half_days"],
        )

        payroll = Payroll(
            employee_id=employee_id,
            month=month_key,
            base_salary=base_salary,
            total_working_days=WORKING_DAYS,
            days_present=summary["total_present"],
            total_absent=summary["total_absent"],
            total_half_days=summary["total_half_days"],
            leave_deductions=amounts["total_deductions"],
            overtime_bonus=0,
            net_salary=amounts["net_salary"],
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
        except Exception as exc:
            db.rollback()
            logger.exception("generate_payroll commit failed employee_id=%s month=%s year=%s", employee_id, month, year)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate payroll") from exc

        db.refresh(payroll)
        logger.debug("generate_payroll success payroll_id=%s employee_id=%s", payroll.id, employee_id)
        return PayrollService._to_response(payroll)


    @staticmethod
    def get_payroll(db: Session, employee_id: UUID, month: int, year: int):
        """Fetch previously generated payroll.

        Notes:
        - payroll snapshots store computed attendance totals, so we do NOT
          require re-reading attendance here.
        - fixes undefined variables/runtime crashes.
        """

        AttendanceService.validate_employee_exists(db, employee_id)
        payroll = PayrollService._get_existing_payroll(db, employee_id, month, year)

        if not payroll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payroll not found for this employee and month",
            )

        # Ensure base salary is usable for response calculations.
        if getattr(payroll, "base_salary", None) is None or payroll.base_salary <= 0:
            raise HTTPException(400, "Invalid payroll base salary")

        return PayrollService._to_response(payroll)


    @staticmethod
    def recalculate_payroll(db: Session, employee_id: UUID, month: int, year: int):
        logger.debug(
            "recalculate_payroll start employee_id=%s month=%s year=%s",
            employee_id,
            month,
            year,
        )

        employee = AttendanceService.validate_employee_exists(db, employee_id)
        base_salary = getattr(employee, "salary", None)
        if base_salary is None or base_salary <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Base salary must be a positive value",
            )

        payroll = PayrollService._get_existing_payroll(db, employee_id, month, year)

        if not payroll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payroll not found. Generate first.",
            )

        attendance = AttendanceService.get_monthly_attendance(
            db=db,
            employee_id=employee_id,
            month=month,
            year=year,
        )

        summary = PayrollService._normalize_attendance_summary(getattr(attendance, "summary", None))

        amounts = PayrollService._calculate_amounts(
            base_salary=base_salary,
            total_present=summary["total_present"],
            total_absent=summary["total_absent"],
            total_half_days=summary["total_half_days"],
        )

        payroll.days_present = summary["total_present"]
        payroll.total_absent = summary["total_absent"]
        payroll.total_half_days = summary["total_half_days"]
        payroll.leave_deductions = amounts["total_deductions"]
        payroll.overtime_bonus = 0
        payroll.net_salary = amounts["net_salary"]
        payroll.status = "recalculated"

        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.exception(
                "recalculate_payroll commit failed employee_id=%s month=%s year=%s",
                employee_id,
                month,
                year,
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to recalculate payroll") from exc

        db.refresh(payroll)
        logger.debug("recalculate_payroll success payroll_id=%s", payroll.id)
        return PayrollService._to_response(payroll)

