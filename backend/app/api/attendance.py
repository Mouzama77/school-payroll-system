from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceReportResponse,
    AttendanceResponse,
)
from app.services.attendance_service import AttendanceService

router = APIRouter()


@router.post(
    "/",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_attendance(
    payload: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return AttendanceService.create(db, payload)


@router.get("/{employee_id}", response_model=AttendanceReportResponse)
def get_monthly_attendance_report(
    employee_id: UUID,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return AttendanceService.get_monthly_report(
        db=db,
        employee_id=employee_id,
        month=month,
        year=year,
    )
