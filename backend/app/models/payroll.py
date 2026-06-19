import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Payroll(Base):
    __tablename__ = "payrolls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id"),
        nullable=False
    )
    month: Mapped[str] = mapped_column(String(7), nullable=False)
    base_salary: Mapped[float] = mapped_column(Float, nullable=False)
    total_working_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    days_present: Mapped[int | None] = mapped_column(Integer, nullable=True)
    leave_deductions: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False
    )
    overtime_bonus: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False
    )
    net_salary: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
