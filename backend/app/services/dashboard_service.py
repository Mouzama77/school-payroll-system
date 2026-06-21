from datetime import date, datetime, timezone

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_employee_for_user
from app.auth.roles import ADMIN, HR
from app.models.attendance import Attendance, AttendanceStatus
from app.models.department import Department
from app.models.employee import Employee
from app.models.payroll import Payroll
from app.models.user import User
from app.schemas.dashboard import (
    AdminDashboardStats,
    EmployeeDashboardStats,
    HRDashboardStats,
    MonthlyReportItem,
    ReportsSummary,
)

WORKING_DAYS = 30


class DashboardService:
    @staticmethod
    def _current_month_year() -> tuple[int, int]:
        today = date.today()
        return today.month, today.year

    @staticmethod
    def get_admin_stats(db: Session) -> AdminDashboardStats:
        month, year = DashboardService._current_month_year()
        month_key = f"{year:04d}-{month:02d}"
        today = date.today()

        return AdminDashboardStats(
            total_employees=db.query(func.count(Employee.id)).scalar() or 0,
            attendance_today=db.query(func.count(Attendance.id))
            .filter(Attendance.date == today)
            .scalar()
            or 0,
            payroll_generated_this_month=db.query(func.count(Payroll.id))
            .filter(Payroll.month == month_key)
            .scalar()
            or 0,
            department_count=db.query(func.count(Department.id)).scalar() or 0,
        )

    @staticmethod
    def get_hr_stats(db: Session) -> HRDashboardStats:
        month, year = DashboardService._current_month_year()
        month_key = f"{year:04d}-{month:02d}"
        today = date.today()

        total_employees = db.query(func.count(Employee.id)).scalar() or 0
        payroll_count = (
            db.query(func.count(Payroll.id)).filter(Payroll.month == month_key).scalar()
            or 0
        )

        return HRDashboardStats(
            total_employees=total_employees,
            pending_payroll_actions=max(total_employees - payroll_count, 0),
            attendance_present_today=db.query(func.count(Attendance.id))
            .filter(
                Attendance.date == today,
                Attendance.status == AttendanceStatus.PRESENT,
            )
            .scalar()
            or 0,
            attendance_absent_today=db.query(func.count(Attendance.id))
            .filter(
                Attendance.date == today,
                Attendance.status == AttendanceStatus.ABSENT,
            )
            .scalar()
            or 0,
        )

    @staticmethod
    def get_employee_stats(db: Session, user: User) -> EmployeeDashboardStats:
        employee = get_employee_for_user(db, user)
        month, year = DashboardService._current_month_year()
        month_key = f"{year:04d}-{month:02d}"

        records = (
            db.query(Attendance)
            .filter(
                Attendance.employee_id == employee.id,
                extract("month", Attendance.date) == month,
                extract("year", Attendance.date) == year,
            )
            .all()
        )

        present_days = sum(
            1 for record in records if record.status == AttendanceStatus.PRESENT
        )
        absent_days = sum(
            1 for record in records if record.status == AttendanceStatus.ABSENT
        )
        half_days = sum(
            1 for record in records if record.status == AttendanceStatus.HALF_DAY
        )
        attendance_percentage = round((present_days / WORKING_DAYS) * 100, 2)

        payroll = (
            db.query(Payroll)
            .filter(
                Payroll.employee_id == employee.id,
                Payroll.month == month_key,
            )
            .first()
        )

        return EmployeeDashboardStats(
            employee_id=employee.id,
            month=month,
            year=year,
            total_working_days=WORKING_DAYS,
            present_days=present_days,
            absent_days=absent_days,
            half_days=half_days,
            attendance_percentage=attendance_percentage,
            net_salary=payroll.net_salary if payroll else None,
            payroll_status=payroll.status if payroll else None,
        )

    @staticmethod
    def get_reports_summary(db: Session, month: int, year: int) -> ReportsSummary:
        month_key = f"{year:04d}-{month:02d}"
        employees = db.query(Employee).order_by(Employee.first_name.asc()).all()
        items: list[MonthlyReportItem] = []
        total_payroll_amount = 0.0
        payrolls_generated = 0

        for employee in employees:
            records = (
                db.query(Attendance)
                .filter(
                    Attendance.employee_id == employee.id,
                    extract("month", Attendance.date) == month,
                    extract("year", Attendance.date) == year,
                )
                .all()
            )
            payroll = (
                db.query(Payroll)
                .filter(
                    Payroll.employee_id == employee.id,
                    Payroll.month == month_key,
                )
                .first()
            )

            if payroll:
                payrolls_generated += 1
                total_payroll_amount += payroll.net_salary or 0

            items.append(
                MonthlyReportItem(
                    employee_id=employee.id,
                    employee_name=f"{employee.first_name} {employee.last_name}",
                    present_days=sum(
                        1
                        for record in records
                        if record.status == AttendanceStatus.PRESENT
                    ),
                    absent_days=sum(
                        1
                        for record in records
                        if record.status == AttendanceStatus.ABSENT
                    ),
                    half_days=sum(
                        1
                        for record in records
                        if record.status == AttendanceStatus.HALF_DAY
                    ),
                    net_salary=payroll.net_salary if payroll else None,
                    payroll_status=payroll.status if payroll else None,
                )
            )

        return ReportsSummary(
            month=month,
            year=year,
            total_employees=len(employees),
            payrolls_generated=payrolls_generated,
            total_payroll_amount=round(total_payroll_amount, 2),
            employees=items,
        )
