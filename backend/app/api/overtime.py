import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.auth.roles import MANAGEMENT_ROLES
from app.db.session import get_db
from app.models.employee import Employee
from app.models.overtime_record import OvertimeRecord
from app.models.user import User
from app.schemas.overtime import OvertimeCreate, OvertimeResponse

router = APIRouter()


@router.post(
    "/",
    response_model=OvertimeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_overtime(
    payload: OvertimeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
):
    # Validate employee exists
    employee = db.query(Employee).filter(Employee.id == payload.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    # Validate date is not in the future
    if payload.date > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Overtime date cannot be in the future",
        )

    # hours > 0 is enforced by the schema validator (raises 422 automatically)

    record = OvertimeRecord(
        id=uuid.uuid4(),
        employee_id=payload.employee_id,
        date=payload.date,
        hours=payload.hours,
        rate_multiplier=payload.rate_multiplier,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
