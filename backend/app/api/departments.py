from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.auth.roles import ADMIN, MANAGEMENT_ROLES
from app.db.session import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)

router = APIRouter(prefix="/departments", tags=["departments"])


def create_department(db: Session, department_data: DepartmentCreate) -> Department:
    existing_department = (
        db.query(Department)
        .filter(func.lower(Department.name) == department_data.name.lower())
        .first()
    )
    if existing_department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department with this name already exists",
        )

    department = Department(
        name=department_data.name.strip(),
        description=department_data.description.strip() if department_data.description else None,
    )
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


def get_departments(db: Session, skip: int = 0, limit: int = 100) -> List[Department]:
    return db.query(Department).offset(skip).limit(limit).all()


def get_department_by_id(db: Session, department_id: UUID) -> Department | None:
    return db.query(Department).filter(Department.id == department_id).first()


def update_department(
    db: Session,
    department: Department,
    department_data: DepartmentUpdate,
) -> Department:
    if department_data.name is not None:
        existing_department = (
            db.query(Department)
            .filter(
                func.lower(Department.name) == department_data.name.lower(),
                Department.id != department.id,
            )
            .first()
        )
        if existing_department:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department with this name already exists",
            )
        department.name = department_data.name.strip()

    if department_data.description is not None:
        department.description = (
            department_data.description.strip()
            if department_data.description.strip()
            else None
        )

    db.commit()
    db.refresh(department)
    return department


def delete_department(db: Session, department: Department) -> None:
    db.delete(department)
    db.commit()


@router.get("", response_model=list[DepartmentResponse])
def list_departments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
):
    return get_departments(db=db, skip=skip, limit=limit)


@router.get("/{department_id}", response_model=DepartmentResponse)
def read_department(
    department_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
):
    department = get_department_by_id(db=db, department_id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )
    return department


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department_endpoint(
    department_data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN)),
):
    return create_department(db=db, department_data=department_data)


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department_endpoint(
    department_id: UUID,
    department_data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN)),
):
    department = get_department_by_id(db=db, department_id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )
    return update_department(
        db=db,
        department=department,
        department_data=department_data,
    )


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department_endpoint(
    department_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN)),
):
    department = get_department_by_id(db=db, department_id=department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )

    from app.models.employee import Employee
    assigned = db.query(Employee).filter(Employee.department_id == department_id).first()
    if assigned:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department is in use and cannot be deleted",
        )

    delete_department(db=db, department=department)
    return None
