from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AdminDashboardStats(BaseModel):
    total_employees: int
    attendance_today: int
    payroll_generated_this_month: int
    department_count: int


class HRDashboardStats(BaseModel):
    total_employees: int
    pending_payroll_actions: int
    attendance_present_today: int
    attendance_absent_today: int


class EmployeeDashboardStats(BaseModel):
    employee_id: UUID
    month: int
    year: int
    total_working_days: int
    present_days: int
    absent_days: int
    half_days: int
    attendance_percentage: float
    net_salary: float | None
    payroll_status: str | None


class MonthlyReportItem(BaseModel):
    employee_id: UUID
    employee_name: str
    present_days: int
    absent_days: int
    half_days: int
    net_salary: float | None
    payroll_status: str | None


class ReportsSummary(BaseModel):
    month: int
    year: int
    total_employees: int
    payrolls_generated: int
    total_payroll_amount: float
    employees: list[MonthlyReportItem]


class InsightItem(BaseModel):
    """A single AI-generated analytics insight for the dashboard."""

    id: str
    type: str  # attendance | leave | payroll | overtime | attention
    severity: str  # info | warning | critical
    title: str
    detail: str
    metric: float | None = None


class DashboardInsights(BaseModel):
    generated_at: datetime
    insights: list[InsightItem]
