import uuid
from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

# Valid day_type values (Req 15.2)
VALID_DAY_TYPES = {"WORKING_DAY", "SCHOOL_HOLIDAY", "EXAM_HOLIDAY", "VACATION"}


class AcademicCalendar(Base):
    """Academic calendar entry — Phase 3 (Req 15.1)."""

    __tablename__ = "academic_calendar"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    day_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
