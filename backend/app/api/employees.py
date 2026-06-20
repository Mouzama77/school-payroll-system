from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.department import Department
from app.models.employee import Employee
from app.models.role import Role
from app.schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate

router = APIRouter()


def get_employee_or_404(db: Session, employee_id: UUID) -> Employee:
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )
    return employee


def validate_department_and_role(db: Session, department_id: UUID, role_id: UUID) -> None:
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid department_id",
        )

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role_id",
        )


def create_employee(db: Session, employee_data: EmployeeCreate) -> Employee:
    validate_department_and_role(
        db=db,
        department_id=employee_data.department_id,
        role_id=employee_data.role_id,
    )

    existing_employee = (
        db.query(Employee).filter(Employee.email == str(employee_data.email)).first()
    )
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee with this email already exists",
        )

    employee = Employee(
        first_name=employee_data.first_name.strip(),
        last_name=employee_data.last_name.strip(),
        email=str(employee_data.email),
        phone=employee_data.phone.strip() if employee_data.phone else None,
        salary=employee_data.salary,
        join_date=employee_data.joining_date,
        department_id=employee_data.department_id,
        role_id=employee_data.role_id,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def get_employees(db: Session, skip: int = 0, limit: int = 100) -> List[Employee]:
    return db.query(Employee).offset(skip).limit(limit).all()


def update_employee(
    db: Session,
    employee: Employee,
    employee_data: EmployeeUpdate,
) -> Employee:
    if employee_data.department_id is not None:
        department = (
            db.query(Department)
            .filter(Department.id == employee_data.department_id)
            .first()
        )
        if not department:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid department_id",
            )
        employee.department_id = employee_data.department_id

    if employee_data.role_id is not None:
        role = db.query(Role).filter(Role.id == employee_data.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role_id",
            )
        employee.role_id = employee_data.role_id

    if employee_data.email is not None:
        email = str(employee_data.email)
        existing_employee = (
            db.query(Employee)
            .filter(Employee.email == email, Employee.id != employee.id)
            .first()
        )
        if existing_employee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee with this email already exists",
            )
        employee.email = email

    if employee_data.first_name is not None:
        employee.first_name = employee_data.first_name.strip()
    if employee_data.last_name is not None:
        employee.last_name = employee_data.last_name.strip()
    if employee_data.phone is not None:
        employee.phone = employee_data.phone.strip() or None
    if employee_data.salary is not None:
        employee.salary = employee_data.salary
    if employee_data.joining_date is not None:
        employee.join_date = employee_data.joining_date

    db.commit()
    db.refresh(employee)
    return employee


def delete_employee(db: Session, employee: Employee) -> None:
    db.delete(employee)
    db.commit()


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee_endpoint(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db),
):
    return create_employee(db=db, employee_data=employee_data)


@router.get("/", response_model=List[EmployeeResponse])
def list_employees(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return get_employees(db=db, skip=skip, limit=limit)


@router.get("/{employee_id}", response_model=EmployeeResponse)
def read_employee(
    employee_id: UUID,
    db: Session = Depends(get_db),
):
    employee = get_employee_or_404(db=db, employee_id=employee_id)
    return employee


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee_endpoint(
    employee_id: UUID,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
):
    employee = get_employee_or_404(db=db, employee_id=employee_id)
    return update_employee(db=db, employee=employee, employee_data=employee_data)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee_endpoint(
    employee_id: UUID,
    db: Session = Depends(get_db),
):
    employee = get_employee_or_404(db=db, employee_id=employee_id)
    delete_employee(db=db, employee=employee)
    return None
