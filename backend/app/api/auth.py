from fastapi import APIRouter, BackgroundTasks, Depends, Request, HTTPException
import time
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_employee_for_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    ResetPasswordRequest,
    ResetPasswordWithOTPRequest,
    VerifyOTPRequest,
    VerifyOTPResponse,
)
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.services.otp_service import OTPService

router = APIRouter()


@router.post("/register", status_code=201)
async def register_user(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    user = AuthService.register_employee_user(
        db=db,
        email=str(payload.email),
        password=payload.password,
        role=payload.role,
    )
    return {
        "message": "User registered successfully",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
        },
    }


@router.post("/login", response_model=LoginResponse)
async def login_user(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = AuthService.authenticate_user(
        db=db,
        email=str(payload.email),
        password=payload.password,
    )
    return AuthService.build_login_response(user)


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Start the OTP-based password reset.

    Generates a secure 6-digit OTP, stores only its hash with a 10-minute
    expiry, and dispatches the email asynchronously via BackgroundTasks.
    Always returns a generic success message to prevent account enumeration.
    """
    result = OTPService.create_otp_for_email(db=db, email=str(payload.email))
    if result is not None:
        otp, to_email = result
        background_tasks.add_task(
            EmailService.send_password_reset_otp, to_email, otp
        )
    return {
        "message": "If an account exists for this email, a verification code has been sent."
    }


@router.post("/verify-otp", response_model=VerifyOTPResponse)
async def verify_otp(
    payload: VerifyOTPRequest,
    db: Session = Depends(get_db),
):
    """Verify the 6-digit OTP and return a short-lived reset token."""
    reset_token = OTPService.verify_otp(
        db=db, email=str(payload.email), otp=payload.otp
    )
    return {"message": "Code verified", "reset_token": reset_token}


@router.post("/reset-password-otp")
async def reset_password_otp(
    payload: ResetPasswordWithOTPRequest,
    db: Session = Depends(get_db),
):
    """Complete the reset using the post-verification reset token."""
    OTPService.reset_password_with_token(
        db=db,
        email=str(payload.email),
        reset_token=payload.reset_token,
        new_password=payload.new_password,
    )
    return {"message": "Password reset successfully"}


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """Legacy token-based reset (kept for backward compatibility)."""
    AuthService.reset_password(
        db=db,
        token=payload.token,
        new_password=payload.new_password,
    )
    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    AuthService.change_password(
        db=db,
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return {"message": "Password changed successfully"}


@router.get("/me")
async def get_current_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "must_change_password": current_user.must_change_password,
        "employee_id": None,
    }

    if current_user.role == "employee":
        employee = get_employee_for_user(db, current_user)
        profile["employee_id"] = str(employee.id)

    return profile
