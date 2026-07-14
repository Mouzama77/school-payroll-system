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

    # ------------------------------------------------------------------ #
    # AI Payroll Insights (Part 5)                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _month_present_rate(db: Session, month: int, year: int) -> float | None:
        records = (
            db.query(Attendance)
            .filter(
                extract("month", Attendance.date) == month,
                extract("year", Attendance.date) == year,
            )
            .all()
        )
        if not records:
            return None
        present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
        return (present / len(records)) * 100

    @staticmethod
    def get_insights(db: Session) -> "DashboardInsights":
        """Generate rule-based analytics insights from live data.

        Insights are produced entirely from backend analytics (no external
        paid APIs). Each insight is only emitted when there is a real signal,
        so an empty list means "nothing noteworthy" rather than an error.
        """
        from app.models.department import Department
        from app.models.leave import Leave, LeaveStatus
        from app.models.overtime_record import OvertimeRecord
        from app.models.payroll import Payroll
        from app.schemas.dashboard import DashboardInsights, InsightItem

        from datetime import date
        import calendar as _calendar

        now = date.today()
        cur_month, cur_year = now.month, now.year
        prev_month, prev_year = (
            (cur_month - 1, cur_year) if cur_month > 1 else (12, cur_year - 1)
        )

        insights: list[InsightItem] = []

        # 1) Attendance trend vs previous month
        cur_rate = DashboardService._month_present_rate(db, cur_month, cur_year)
        prev_rate = DashboardService._month_present_rate(db, prev_month, prev_year)
        if cur_rate is not None and prev_rate is not None and prev_rate > 0:
            drop = prev_rate - cur_rate
            if drop >= 3:
                insights.append(
                    InsightItem(
                        id="attendance_drop",
                        type="attendance",
                        severity="warning",
                        title="Attendance dropped this month",
                        detail=(
                            f"Present rate fell from {prev_rate:.1f}% to "
                            f"{cur_rate:.1f}% (a {drop:.1f}% drop) versus last month."
                        ),
                        metric=round(drop, 1),
                    )
                )

        # 2) Excessive leave this month
        leave_recs = (
            db.query(Leave)
            .filter(
                Leave.status == LeaveStatus.APPROVED,
                extract("month", Leave.start_date) == cur_month,
                extract("year", Leave.start_date) == cur_year,
            )
            .all()
        )
        leave_days_by_emp: dict = {}
        for lv in leave_recs:
            days = (lv.end_date - lv.start_date).days + 1
            leave_days_by_emp[lv.employee_id] = (
                leave_days_by_emp.get(lv.employee_id, 0) + days
            )
        excessive = [eid for eid, d in leave_days_by_emp.items() if d >= 5]
        if excessive:
            insights.append(
                InsightItem(
                    id="excessive_leave",
                    type="leave",
                    severity="warning",
                    title=f"{len(excessive)} employee(s) have excessive leave",
                    detail=(
                        f"{len(excessive)} employee(s) have taken 5+ leave days "
                        f"this month and may need a follow-up."
                    ),
                    metric=len(excessive),
                )
            )

        # 3) Projected payroll for next month
        active_emps = db.query(Employee).filter(Employee.status == "active").all()
        projected = sum((e.salary or 0) for e in active_emps)
        if projected > 0:
            insights.append(
                InsightItem(
                    id="projected_payroll",
                    type="payroll",
                    severity="info",
                    title="Projected payroll for next month",
                    detail=(
                        f"Estimated outlay of {projected:,.0f} for "
                        f"{len(active_emps)} active employee(s) based on base salaries."
                    ),
                    metric=round(projected, 2),
                )
            )

        # 4) Department with highest overtime
        ot_recs = db.query(OvertimeRecord).all()
        if ot_recs:
            emp_rows = db.query(Employee).all()
            dept_by_emp = {e.id: e.department_id for e in emp_rows}
            dept_name = {d.id: d.name for d in db.query(Department).all()}
            hours_by_dept: dict = {}
            for r in ot_recs:
                did = dept_by_emp.get(r.employee_id)
                if did:
                    hours_by_dept[did] = hours_by_dept.get(did, 0) + (r.hours or 0)
            if hours_by_dept:
                top_id, top_hours = max(hours_by_dept.items(), key=lambda kv: kv[1])
                insights.append(
                    InsightItem(
                        id="overtime_dept",
                        type="overtime",
                        severity="info",
                        title=f"Highest overtime: {dept_name.get(top_id, 'Unknown')}",
                        detail=(
                            f"{dept_name.get(top_id, 'Unknown')} logged the most "
                            f"overtime ({top_hours:.1f}h) across all records."
                        ),
                        metric=round(top_hours, 1),
                    )
                )

        # 5) Employees requiring HR attention (low attendance or excessive leave)
        attention = []
        for e in active_emps:
            recs = (
                db.query(Attendance)
                .filter(
                    Attendance.employee_id == e.id,
                    extract("month", Attendance.date) == cur_month,
                    extract("year", Attendance.date) == cur_year,
                )
                .all()
            )
            if recs:
                present = sum(1 for r in recs if r.status == AttendanceStatus.PRESENT)
                rate = (present / len(recs)) * 100
                if rate < 60:
                    attention.append(f"{e.first_name} {e.last_name}")
            if e.id in excessive and f"{e.first_name} {e.last_name}" not in attention:
                attention.append(f"{e.first_name} {e.last_name}")
        if attention:
            listed = ", ".join(attention[:5])
            if len(attention) > 5:
                listed += ", …"
            insights.append(
                InsightItem(
                    id="hr_attention",
                    type="attention",
                    severity="critical",
                    title=f"{len(attention)} employee(s) require HR attention",
                    detail=f"Low attendance or excessive leave: {listed}.",
                    metric=len(attention),
                )
            )

        return DashboardInsights(
            generated_at=datetime.now(timezone.utc),
            insights=insights,
        )
