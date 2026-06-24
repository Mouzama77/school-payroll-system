from fastapi import APIRouter, Depends, Request, HTTPException
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
)
from app.services.auth_service import AuthService

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
    db: Session = Depends(get_db),
):
    return AuthService.request_password_reset(db=db, email=str(payload.email))


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
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
