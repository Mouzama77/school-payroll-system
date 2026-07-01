from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.leave import LeaveStatus, LeaveType


class LeaveCreate(BaseModel):
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: Optional[str] = None

    @model_validator(mode="after")
    def end_date_not_before_start(self) -> "LeaveCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class LeaveUpdate(BaseModel):
    status: LeaveStatus


class LeaveOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    leave_type: LeaveType
    status: LeaveStatus
    start_date: date
    end_date: date
    reason: Optional[str]
