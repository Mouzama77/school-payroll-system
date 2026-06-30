from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    HALF_DAY = "HALF_DAY"
    ON_LEAVE = "ON_LEAVE"
    LATE = "LATE"


# Statuses accepted via POST /attendance — ON_LEAVE is set automatically by leave approval
class AttendanceCreateStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    HALF_DAY = "HALF_DAY"
    LATE = "LATE"


# Statuses that HR/Admin may override TO (ON_LEAVE is set automatically, never manually)
OVERRIDABLE_STATUSES = {
    AttendanceStatus.PRESENT,
    AttendanceStatus.ABSENT,
    AttendanceStatus.HALF_DAY,
    AttendanceStatus.LATE,
}


class AttendanceCreate(BaseModel):
    employee_id: UUID
    date: date
    status: AttendanceCreateStatus = AttendanceCreateStatus.PRESENT


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    date: date
    status: AttendanceStatus
    created_at: datetime
    updated_at: datetime

    # Override audit fields
    is_override: bool
    override_reason: str | None
    overridden_by: UUID | None
    overridden_at: datetime | None


class AttendanceOverrideRequest(BaseModel):
    """Payload for HR/Admin overriding an ON_LEAVE attendance record."""

    status: AttendanceStatus
    reason: str

    @field_validator("status")
    @classmethod
    def status_must_not_be_on_leave(cls, v: AttendanceStatus) -> AttendanceStatus:
        if v == AttendanceStatus.ON_LEAVE:
            raise ValueError("Cannot override to ON_LEAVE; that status is set automatically")
        return v

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Override reason is required and cannot be blank")
        return v.strip()


class AttendanceSummary(BaseModel):
    total_present: int
    total_absent: int
    total_half_days: int


class MonthlyAttendanceResponse(BaseModel):
    employee_id: UUID
    month: int
    year: int
    records: list[AttendanceResponse]
    summary: AttendanceSummary
