from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PayrollGenerateRequest(BaseModel):
    employee_id: UUID
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2000)


class PayrollResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    month: int
    year: int
    base_salary: float
    total_working_days: int
    total_present: int
    total_absent: int
    total_half_days: int
    daily_salary: float
    absent_deductions: float
    half_day_deductions: float
    leave_deductions: float
    total_deductions: float
    net_salary: float
    status: str
    created_at: datetime
