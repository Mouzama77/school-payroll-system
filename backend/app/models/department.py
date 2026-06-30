from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, Text, UniqueConstraint, UUID as SQLUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text as sa_text

from app.db.session import Base


class Department(Base):
    __tablename__ = "departments"
    __table_args__ = (
        # Reflect the existing unique constraint on code that is in the DB
        UniqueConstraint("code", name="uq_departments_code"),
    )

    id: Mapped[UUID] = mapped_column(
        SQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    # DB stores as VARCHAR(255)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa_text("now()"),
        nullable=False,
    )

    # Extra columns present in DB — mirrored here to prevent autogenerate DROP
    code: Mapped[str | None] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=sa_text("true"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sa_text("now()"),
    )
