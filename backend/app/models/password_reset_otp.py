import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text as sa_text

from app.db.session import Base


class PasswordResetOTP(Base):
    """A hashed, time-limited one-time password used for password reset.

    The plaintext OTP is never stored — only a bcrypt hash. Each row tracks
    verification attempts (for lockout) and whether it has been consumed.
    """

    __tablename__ = "password_reset_otps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # bcrypt hash of the 6-digit OTP
    otp_hash: Mapped[str] = mapped_column(String, nullable=False)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=sa_text("0"),
        default=0,
    )

    # Set True once the OTP has been verified successfully
    verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=sa_text("false"),
        default=False,
    )

    # Set True once the OTP has been used to complete a reset (or superseded)
    consumed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=sa_text("false"),
        default=False,
    )

    # Short-lived token issued after successful verification; the final
    # reset-password call presents this instead of the OTP.
    reset_token_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    reset_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa_text("now()"),
        nullable=False,
    )
