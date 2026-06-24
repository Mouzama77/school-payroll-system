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
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceOverrideRequest,
    AttendanceResponse,
    MonthlyAttendanceResponse,
)
from app.services.attendance_service import AttendanceService

router = APIRouter()


@router.post(
    "/",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def mark_attendance(
    payload: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
):
    return AttendanceService.mark_attendance(db, payload, actor_id=current_user.id)


@router.put(
    "/{attendance_id}/override",
    response_model=AttendanceResponse,
    summary="Override an attendance record (HR/Admin only)",
)
def override_attendance(
    attendance_id: UUID,
    payload: AttendanceOverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
):
    """Override the status of an existing attendance record.

    - Only HR and Admin may call this endpoint.
    - A mandatory reason must be provided.
    - The new status cannot be ON_LEAVE (that is set automatically on leave approval).
    - Full audit data (who, when, why) is stored on the record.
    """
    return AttendanceService.override_attendance(
        db=db,
        attendance_id=attendance_id,
        new_status=payload.status,
        reason=payload.reason,
        overriding_user_id=current_user.id,
    )


@router.get("/{employee_id}", response_model=MonthlyAttendanceResponse)
def get_monthly_attendance(
    employee_id: UUID,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assert_employee_access(db, current_user, employee_id)
    return AttendanceService.get_monthly_attendance(
        db=db,
        employee_id=employee_id,
        month=month,
        year=year,
    )
