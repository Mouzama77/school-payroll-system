from datetime import date, datetime
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
    designation_id: UUID | None = None  # Req 13.5 — nullable, validated against designations


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    salary: float
    joining_date: date = Field(validation_alias="join_date")
    department_id: UUID
    role_id: UUID
    designation_id: UUID | None = None
    status: str = "active"
    created_at: datetime
