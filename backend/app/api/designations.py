"""Designations API — Phase 2 (Req 13.1–13.3)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.auth.roles import MANAGEMENT_ROLES
from app.db.session import get_db
from app.models.designation import Designation
from app.models.user import User

router = APIRouter(prefix="/designations", tags=["Designations"])


class DesignationCreate(BaseModel):
    name: str
    description: str | None = None


class DesignationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None


@router.post("", response_model=DesignationResponse, status_code=status.HTTP_201_CREATED)
def create_designation(
    data: DesignationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
):
    """Create a designation. Case-insensitive duplicate check → 409 (Req 13.2, 13.3)."""
    existing = (
        db.query(Designation)
        .filter(func.lower(Designation.name) == data.name.strip().lower())
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Designation with this name already exists",
        )
    desig = Designation(name=data.name.strip(), description=data.description)
    db.add(desig)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Designation with this name already exists",
        )
    db.refresh(desig)
    return desig


@router.get("", response_model=list[DesignationResponse])
def list_designations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
):
    return db.query(Designation).order_by(Designation.name).all()
