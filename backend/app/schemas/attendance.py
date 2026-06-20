from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    HALF_DAY = "HALF_DAY"


class AttendanceCreate(BaseModel):
    employee_id: UUID
    date: date
    status: AttendanceStatus = AttendanceStatus.PRESENT


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    date: date
    status: AttendanceStatus
    created_at: datetime
    updated_at: datetime


class AttendanceSummary(BaseModel):
    total_present: int
    total_absent: int
    total_half_days: int


class AttendanceReportResponse(BaseModel):
    employee_id: UUID
    month: int
    year: int
    records: list[AttendanceResponse]
    summary: AttendanceSummary
