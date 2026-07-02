from datetime import date
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# Req 15.2 — only these four values are accepted; anything else → HTTP 422
DayType = Literal["WORKING_DAY", "SCHOOL_HOLIDAY", "EXAM_HOLIDAY", "VACATION"]


class AcademicCalendarCreate(BaseModel):
    date: date
    day_type: DayType
    description: Optional[str] = None


class AcademicCalendarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    date: date
    day_type: str
    description: Optional[str] = None
