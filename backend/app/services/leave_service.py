from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session

from app.models.attendance import Attendance, AttendanceStatus
from app.models.audit_log import AuditLog
from app.models.leave import Leave, LeaveStatus


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


def update_leave_status(db: Session, leave_id: UUID, new_status, approved_by: UUID):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Leave request not found",
        )

    leave.status = new_status
    leave.approved_by = approved_by

    # When a leave is approved, automatically create or update attendance records
    # for each calendar day in the leave range with status ON_LEAVE.
    # Rules:
    #   - Existing records that have been manually overridden (is_override=True)
    #     are never touched — the override takes precedence over the leave.
    #   - Existing non-overridden records are updated to ON_LEAVE.
    #   - Missing records are created with ON_LEAVE.
    # Everything happens inside the same transaction; a failure rolls back all changes.
    if new_status == LeaveStatus.APPROVED:
        current_date = leave.start_date
        while current_date <= leave.end_date:
            existing = (
                db.query(Attendance)
                .filter(
                    Attendance.employee_id == leave.employee_id,
                    Attendance.date == current_date,
                )
                .first()
            )
            if existing:
                # Respect manual overrides — never overwrite them on leave approval.
                if existing.is_override:
                    current_date += timedelta(days=1)
                    continue
                existing.status = AttendanceStatus.ON_LEAVE
            else:
                db.add(
                    Attendance(
                        employee_id=leave.employee_id,
                        date=current_date,
                        status=AttendanceStatus.ON_LEAVE,
                    )
                )
            current_date += timedelta(days=1)

    # Determine audit action label.
    action = (
        "LEAVE_APPROVED" if new_status == LeaveStatus.APPROVED else "LEAVE_REJECTED"
    )
    db.add(
        AuditLog(
            actor_id=approved_by,
            action=action,
            entity_type="leave",
            entity_id=leave_id,
            detail=f"Leave {leave_id} set to {new_status.value} by user {approved_by}",
        )
    )

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(leave)
    return leave
