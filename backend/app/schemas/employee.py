from datetime import date, datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmployeeCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = None
    salary: float = Field(..., ge=0)
    joining_date: date
    department_id: UUID
    role_id: UUID


class EmployeeUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = None
    salary: float | None = Field(None, ge=0)
    joining_date: date | None = None
    department_id: UUID | None = None
    role_id: UUID | None = None


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    salary: float
    joining_date: date = Field(default_factory=date.today)
    department_id: UUID
    role_id: UUID
    created_at: datetime
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
