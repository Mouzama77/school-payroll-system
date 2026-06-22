from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    assert_employee_access,
    get_current_user,
    require_roles,
)
from app.auth.roles import MANAGEMENT_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.payroll import PayrollGenerateRequest, PayrollResponse
from app.services.payroll_service import PayrollService

router = APIRouter()


@router.post(
    "/generate",
    response_model=PayrollResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_payroll(
    payload: PayrollGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
):
    return PayrollService.generate_payroll(
        db=db,
        employee_id=payload.employee_id,
        month=payload.month,
        year=payload.year,
    )


@router.patch(
    "/{employee_id}/recalculate",
    response_model=PayrollResponse,
    summary="Recalculate payroll using current attendance data (HR/Admin only)",
)
def recalculate_payroll(
    employee_id: UUID,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
):
    """Recalculate an existing payroll snapshot after attendance overrides.

    Re-reads attendance records (which reflect any manual overrides) and
    updates the stored payroll figures in place. Requires payroll to have
    been generated first via POST /payroll/generate.
    """
    return PayrollService.recalculate_payroll(
        db=db,
        employee_id=employee_id,
        month=month,
        year=year,
    )


@router.get("/{employee_id}", response_model=PayrollResponse)
def get_payroll(
    employee_id: UUID,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assert_employee_access(db, current_user, employee_id)
    return PayrollService.get_payroll(
        db=db,
        employee_id=employee_id,
        month=month,
        year=year,
    )
