from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_employee_for_user, require_roles
from app.auth.roles import MANAGEMENT_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.leave import LeaveCreate, LeaveOut, LeaveUpdate
from app.services.leave_service import (
    create_leave,
    get_all_leaves,
    get_employee_leaves,
    update_leave_status,
)

router = APIRouter(prefix="/leaves", tags=["Leaves"])


# Employee: create leave request
@router.post("/", response_model=LeaveOut)
def request_leave(
    data: LeaveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    employee = get_employee_for_user(db, current_user)
    return create_leave(db, employee.id, data)


# Employee: view own leaves
@router.get("/my", response_model=list[LeaveOut])
def my_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    employee = get_employee_for_user(db, current_user)
    return get_employee_leaves(db, employee.id)


# Admin/HR: view all leaves
@router.get("/", response_model=list[LeaveOut])
def all_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
):
    return get_all_leaves(db)


# Admin/HR: approve/reject
@router.put("/{leave_id}", response_model=LeaveOut)
def update_leave(
    leave_id: UUID,
    data: LeaveUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
):
    return update_leave_status(db, leave_id, data.status, current_user.id)
