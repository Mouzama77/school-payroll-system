import uuid
from datetime import datetime, date, timezone, time

from sqlalchemy import String, Date, Float, ForeignKey, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id"),
        nullable=False
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id"),
        nullable=False
    )

    salary: Mapped[float] = mapped_column(Float, nullable=False)

    # ✅ FIXED (IMPORTANT FOR PAYROLL LOGIC)
    reporting_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(9, 30))

    join_date: Mapped[date] = mapped_column(default=date.today)

    status: Mapped[str] = mapped_column(String(20), default="active")

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )