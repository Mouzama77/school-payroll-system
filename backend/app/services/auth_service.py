import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.auth.hashing import hash_password, verify_password
from app.auth.jwt import create_access_token
from app.core.config import settings
from app.models.user import User


class AuthService:
    """Central authentication / user-management service."""

    # ------------------------------------------------------------------ #
    # Registration & user creation                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def register_employee_user(db, email: str, password: str, role: str) -> User:
        """Register a new user (public self-registration path)."""
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role,
            must_change_password=False,
        )
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Email already registered")
        db.refresh(user)
        return user

    @staticmethod
    def create_user(
        db,
        email: str,
        password: str,
        role: str,
        must_change_password: bool = True,
        actor_role: str = "admin",
    ) -> User:
        """Admin-initiated user creation."""
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role,
            must_change_password=must_change_password,
        )
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Email already registered")
        db.refresh(user)
        return user

    # ------------------------------------------------------------------ #
    # Authentication                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def authenticate_user(db, email: str, password: str) -> User:
        """Verify credentials and return the user, or raise HTTP 401."""
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        return user

    @staticmethod
    def build_login_response(user: User) -> dict:
        """Build the JWT login response payload."""
        token = create_access_token({"sub": str(user.id), "role": user.role})
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": user.role,
            "must_change_password": user.must_change_password,
        }

    # ------------------------------------------------------------------ #
    # Password management                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def change_password(db, user: User, current_password: str, new_password: str) -> None:
        """Allow an authenticated user to change their own password."""
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        user.password_hash = hash_password(new_password)
        user.must_change_password = False
        db.commit()

    @staticmethod
    def admin_reset_password(
        db,
        user: User,
        new_password: str,
        must_change_password: bool = True,
    ) -> None:
        """Admin forcibly resets a user's password."""
        user.password_hash = hash_password(new_password)
        user.must_change_password = must_change_password
        db.commit()

    # ------------------------------------------------------------------ #
    # Password reset (token-based)                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def request_password_reset(db, email: str) -> dict:
        """Generate a reset token, store its hash, and return a message.

        In Phase 1 there is no email delivery — the raw token is included in
        the response detail so developers can test the flow directly.
        """
        user = db.query(User).filter(User.email == email).first()
        # Always return success to avoid user-enumeration
        if not user:
            return {"message": "Password reset email sent"}

        raw_token = secrets.token_urlsafe(32)
        user.reset_token_hash = hash_password(raw_token)
        user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
        )
        db.commit()

        # Dev convenience: return the raw token in the response
        return {
            "message": "Password reset email sent",
            "detail": f"[dev] reset token: {raw_token}",
        }

    @staticmethod
    def reset_password(db, token: str, new_password: str) -> None:
        """Validate the reset token and set a new password."""
        now = datetime.now(timezone.utc)

        # Find candidate users that have a non-expired token
        candidates = (
            db.query(User)
            .filter(
                User.reset_token_hash.isnot(None),
                User.reset_token_expires_at > now,
            )
            .all()
        )

        matched_user = None
        for candidate in candidates:
            if verify_password(token, candidate.reset_token_hash):
                matched_user = candidate
                break

        if not matched_user:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")

        matched_user.password_hash = hash_password(new_password)
        matched_user.reset_token_hash = None
        matched_user.reset_token_expires_at = None
        matched_user.must_change_password = False
        db.commit()
