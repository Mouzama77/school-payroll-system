import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.hashing import hash_password, verify_password
from app.auth.jwt import create_access_token
from app.auth.roles import ADMIN, EMPLOYEE, HR, VALID_ROLES
from app.core.config import settings
from app.models.employee import Employee
from app.models.user import User
from app.schemas.auth import LoginResponse


class AuthService:
    @staticmethod
    def build_login_response(user: User) -> LoginResponse:
        access_token = create_access_token(
            {
                "sub": str(user.id),
                "user_id": str(user.id),
                "email": user.email,
                "role": user.role,
            }
        )
        return LoginResponse(
            access_token=access_token,
            role=user.role,
            must_change_password=user.must_change_password,
        )

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive",
            )
        return user

    @staticmethod
    def register_employee_user(
        db: Session,
        email: str,
        password: str,
        role: str = EMPLOYEE,
    ) -> User:
        if role != EMPLOYEE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only employee self-registration is allowed on this endpoint",
            )

        if role not in VALID_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(sorted(VALID_ROLES))}",
            )

        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        employee = db.query(Employee).filter(Employee.email == email).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No employee record found for this email",
            )

        user = User(
            email=email,
            hashed_password=hash_password(password),
            role=EMPLOYEE,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password: str,
        role: str,
        must_change_password: bool = True,
        actor_role: str | None = None,
    ) -> User:
        if role not in VALID_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(sorted(VALID_ROLES))}",
            )

        if actor_role == HR and role in {ADMIN, HR}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="HR cannot create admin or HR accounts",
            )

        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        if role == EMPLOYEE:
            employee = db.query(Employee).filter(Employee.email == email).first()
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Employee accounts require a matching employee email",
                )

        user = User(
            email=email,
            hashed_password=hash_password(password),
            role=role,
            must_change_password=must_change_password,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def request_password_reset(db: Session, email: str) -> dict:
        user = db.query(User).filter(User.email == email).first()
        response = {
            "message": "If the email exists, a password reset link has been generated.",
        }

        if not user:
            return response

        token = secrets.token_urlsafe(32)
        user.reset_token_hash = hash_password(token)
        user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
        )
        db.commit()

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        if settings.DEBUG:
            response["reset_token"] = token
            response["reset_url"] = reset_url

        return response

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> None:
        users = db.query(User).filter(User.reset_token_hash.isnot(None)).all()
        user = None
        for candidate in users:
            if (
                candidate.reset_token_expires_at
                and candidate.reset_token_expires_at > datetime.now(timezone.utc)
                and verify_password(token, candidate.reset_token_hash)
            ):
                user = candidate
                break

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        user.hashed_password = hash_password(new_password)
        user.must_change_password = False
        user.reset_token_hash = None
        user.reset_token_expires_at = None
        db.commit()

    @staticmethod
    def change_password(
        db: Session,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        user.hashed_password = hash_password(new_password)
        user.must_change_password = False
        db.commit()

    @staticmethod
    def admin_reset_password(
        db: Session,
        user: User,
        new_password: str,
        must_change_password: bool = True,
    ) -> None:
        user.hashed_password = hash_password(new_password)
        user.must_change_password = must_change_password
        user.reset_token_hash = None
        user.reset_token_expires_at = None
        db.commit()
