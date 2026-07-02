"""Academic Calendar API — Phase 3 (Req 15.1, 15.2)."""

from datetime import date as DateType
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.auth.roles import ADMIN
from app.db.session import get_db
from app.models.academic_calendar import AcademicCalendar, VALID_DAY_TYPES
from app.models.user import User

router = APIRouter(prefix="/academic-calendar", tags=["Academic Calendar"])


class AcademicCalendarCreate(BaseModel):
    date: DateType
    day_type: str
    description: str | None = None

    @field_validator("day_type")
    @classmethod
    def validate_day_type(cls, v: str) -> str:
        """Req 15.2 — reject values outside the four allowed types."""
        if v not in VALID_DAY_TYPES:
            raise ValueError(
                f"day_type must be one of: {', '.join(sorted(VALID_DAY_TYPES))}"
            )
        return v


class AcademicCalendarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    date: DateType
    day_type: str
    description: str | None


@router.post(
    "/",
    response_model=AcademicCalendarResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_calendar_entry(
    data: AcademicCalendarCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN)),
):
    """Create a calendar entry. Duplicate date → 409."""
    existing = db.query(AcademicCalendar).filter(
        AcademicCalendar.date == data.date
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Calendar entry for {data.date} already exists",
        )
    entry = AcademicCalendar(
        date=data.date,
        day_type=data.day_type,
        description=data.description,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/", response_model=list[AcademicCalendarResponse])
def list_calendar_entries(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN)),
):
    return db.query(AcademicCalendar).order_by(AcademicCalendar.date).all()
