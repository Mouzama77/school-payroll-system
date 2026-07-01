import uuid
from datetime import date

from sqlalchemy import Date, Double, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class OvertimeRecord(Base):
    __tablename__ = "overtime_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    date: Mapped[date] = mapped_column(Date, nullable=False)

    hours: Mapped[float] = mapped_column(Double, nullable=False)

    rate_multiplier: Mapped[float] = mapped_column(
        Double,
        nullable=False,
        default=1.5,
    )

    employee = relationship("Employee")
