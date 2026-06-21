from uuid import UUID

from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session

from app.models.leave import Leave


def create_leave(db: Session, employee_id, data):
    leave = Leave(
        employee_id=employee_id,
        leave_type=data.leave_type,
        start_date=data.start_date,
        end_date=data.end_date,
        reason=data.reason,
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return leave


def get_employee_leaves(db: Session, employee_id):
    return db.query(Leave).filter(Leave.employee_id == employee_id).all()


def get_all_leaves(db: Session):
    return db.query(Leave).all()


def update_leave_status(db: Session, leave_id: UUID, status, approved_by: UUID):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Leave request not found",
        )

    leave.status = status
    leave.approved_by = approved_by

    db.commit()
    db.refresh(leave)
    return leave
