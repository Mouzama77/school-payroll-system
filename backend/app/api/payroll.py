from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
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
    current_user=Depends(get_current_user),
):
    return PayrollService.generate_payroll(
        db=db,
        employee_id=payload.employee_id,
        month=payload.month,
        year=payload.year,
    )


@router.get("/{employee_id}", response_model=PayrollResponse)
def get_payroll(
    employee_id: UUID,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return PayrollService.get_payroll(
        db=db,
        employee_id=employee_id,
        month=month,
        year=year,
    )
