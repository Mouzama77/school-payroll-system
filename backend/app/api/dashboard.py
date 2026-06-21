from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.auth.roles import ADMIN, EMPLOYEE, HR, MANAGEMENT_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import (
    AdminDashboardStats,
    EmployeeDashboardStats,
    HRDashboardStats,
    ReportsSummary,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/admin", response_model=AdminDashboardStats)
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN)),
):
    return DashboardService.get_admin_stats(db)


@router.get("/hr", response_model=HRDashboardStats)
def hr_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(HR)),
):
    return DashboardService.get_hr_stats(db)


@router.get("/employee", response_model=EmployeeDashboardStats)
def employee_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(EMPLOYEE)),
):
    return DashboardService.get_employee_stats(db, current_user)


@router.get("/reports", response_model=ReportsSummary)
def monthly_reports(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
):
    return DashboardService.get_reports_summary(db, month, year)
