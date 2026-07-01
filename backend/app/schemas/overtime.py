from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class OvertimeCreate(BaseModel):
    employee_id: UUID
    date: date
    hours: float
    rate_multiplier: float = 1.5

    @field_validator("hours")
    @classmethod
    def hours_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("hours must be greater than 0")
        return v


class OvertimeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    date: date
    hours: float
    rate_multiplier: float
