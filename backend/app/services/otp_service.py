"""OTP-based password reset service.

Handles secure generation, hashing, storage, verification (with attempt
lockout and rate limiting), and final password reset. The plaintext OTP is
never persisted — only a bcrypt hash. After successful verification a short-
lived reset token is issued so the final password change does not require
re-sending the OTP.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.hashing import hash_password, verify_password
from app.core.config import settings
from app.models.password_reset_otp import PasswordResetOTP
from app.models.user import User


class OTPService:
    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def generate_otp() -> str:
        """Generate a cryptographically secure numeric OTP."""
        length = settings.OTP_LENGTH
        # secrets.randbelow avoids modulo bias; zero-pad to fixed length.
        upper = 10 ** length
        return str(secrets.randbelow(upper)).zfill(length)

    @staticmethod
    def _active_otp(db: Session, user_id) -> PasswordResetOTP | None:
        """Return the most recent non-consumed OTP row for a user, if any."""
        return (
            db.query(PasswordResetOTP)
            .filter(
                PasswordResetOTP.user_id == user_id,
                PasswordResetOTP.consumed.is_(False),
            )
            .order_by(PasswordResetOTP.created_at.desc())
            .first()
        )

    # ------------------------------------------------------------------ #
    # Create / send                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_otp_for_email(db: Session, email: str) -> tuple[str, str] | None:
        """Create and persist a hashed OTP for the user with `email`.

        Returns (plaintext_otp, email) so the caller can dispatch the email in
        a background task, or None when no user exists (caller should still
        respond generically to avoid user enumeration).

        Raises HTTP 429 when the per-email resend cooldown is violated.
        """
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None

        # Rate limiting: block rapid re-requests for the same account.
        existing = OTPService._active_otp(db, user.id)
        if existing is not None:
            age = (OTPService._now() - existing.created_at).total_seconds()
            if age < settings.OTP_RESEND_COOLDOWN_SECONDS:
                retry_in = int(settings.OTP_RESEND_COOLDOWN_SECONDS - age)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Please wait {retry_in}s before requesting another code.",
                )
            # Supersede any previous active OTP.
            existing.consumed = True

        otp = OTPService.generate_otp()
        record = PasswordResetOTP(
            user_id=user.id,
            otp_hash=hash_password(otp),
            expires_at=OTPService._now()
            + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
            attempts=0,
            verified=False,
            consumed=False,
        )
        db.add(record)
        db.commit()
        return otp, user.email

    # ------------------------------------------------------------------ #
    # Verify                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def verify_otp(db: Session, email: str, otp: str) -> str:
        """Verify an OTP and return a short-lived reset token on success."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired code",
            )

        record = OTPService._active_otp(db, user.id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired code",
            )

        # Expiry check
        if record.expires_at <= OTPService._now():
            record.consumed = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Code has expired. Please request a new one.",
            )

        # Attempt lockout
        if record.attempts >= settings.OTP_MAX_ATTEMPTS:
            record.consumed = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many incorrect attempts. Please request a new code.",
            )

        if not verify_password(otp, record.otp_hash):
            record.attempts += 1
            remaining = max(settings.OTP_MAX_ATTEMPTS - record.attempts, 0)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid code. {remaining} attempt(s) remaining.",
            )

        # Success: issue a short-lived reset token bound to this OTP row.
        reset_token = secrets.token_urlsafe(32)
        record.verified = True
        record.reset_token_hash = hash_password(reset_token)
        record.reset_token_expires_at = OTPService._now() + timedelta(
            minutes=settings.OTP_RESET_TOKEN_EXPIRE_MINUTES
        )
        db.commit()
        return reset_token

    # ------------------------------------------------------------------ #
    # Reset                                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def reset_password_with_token(
        db: Session, email: str, reset_token: str, new_password: str
    ) -> None:
        """Complete the password reset using the post-verification token."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset session",
            )

        record = (
            db.query(PasswordResetOTP)
            .filter(
                PasswordResetOTP.user_id == user.id,
                PasswordResetOTP.consumed.is_(False),
                PasswordResetOTP.verified.is_(True),
                PasswordResetOTP.reset_token_hash.isnot(None),
            )
            .order_by(PasswordResetOTP.created_at.desc())
            .first()
        )

        if (
            record is None
            or record.reset_token_expires_at is None
            or record.reset_token_expires_at <= OTPService._now()
            or not verify_password(reset_token, record.reset_token_hash)
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset session. Please restart.",
            )

        # Apply the new password and consume the OTP row.
        user.password_hash = hash_password(new_password)
        user.must_change_password = False
        record.consumed = True
        record.reset_token_hash = None
        record.reset_token_expires_at = None

        # Invalidate any legacy token-based reset fields too, for safety.
        user.reset_token_hash = None
        user.reset_token_expires_at = None

        db.commit()
