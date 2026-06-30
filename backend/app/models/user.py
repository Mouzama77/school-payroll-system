import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text as sa_text

from app.db.session import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        # Reflect the existing unique index on invitation_token that is in the DB
        Index("ix_users_invitation_token", "invitation_token", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    email: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
    )
    # Maps to the actual DB column name
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(
        String(20),
        default="employee",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    must_change_password: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    reset_token_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    reset_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # Match DB: TIMESTAMP(timezone=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa_text("now()"),
        nullable=False,
    )

    # Extra columns present in DB — mirrored here to match DB reality
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa_text("now()"),
        nullable=False,
    )
    # DB has this as a registration_status ENUM; declare as String to avoid
    # ALTER TYPE DDL — the ENUM values cast transparently via Python strings.
    registration_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default=sa_text("'ACTIVE'"),
    )
    invitation_token: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    invitation_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=sa_text("false"),
    )
