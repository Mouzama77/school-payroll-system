"""
Seed demo data for the School Payroll System.

Usage:
    cd backend
    python -m scripts.seed_demo_data
"""

from datetime import date

from app.auth.hashing import hash_password
from app.db.session import SessionLocal
from app.models.attendance import Attendance, AttendanceStatus
from app.models.department import Department
from app.models.employee import Employee
from app.models.role import Role
from app.models.user import User

DEMO_PASSWORDS = {
    "admin@school.com": "Admin@2026!",
    "hr@school.com": "Hr@2026!",
    "teacher@school.com": "Teacher@2026!",
}


def get_or_create_department(db, name: str, description: str) -> Department:
    department = db.query(Department).filter(Department.name == name).first()
    if department:
        return department
    department = Department(name=name, description=description)
    db.add(department)
    db.flush()
    return department


def get_or_create_job_role(db, name: str, description: str) -> Role:
    role = db.query(Role).filter(Role.name == name).first()
    if role:
        return role
    role = Role(name=name, description=description)
    db.add(role)
    db.flush()
    return role


def get_or_create_user(db, email: str, role: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(
        email=email,
        hashed_password=hash_password(DEMO_PASSWORDS[email]),
        role=role,
        must_change_password=True,
    )
    db.add(user)
    db.flush()
    return user


def get_or_create_employee(
    db,
    *,
    first_name: str,
    last_name: str,
    email: str,
    salary: float,
    department: Department,
    job_role: Role,
) -> Employee:
    employee = db.query(Employee).filter(Employee.email == email).first()
    if employee:
        return employee
    employee = Employee(
        first_name=first_name,
        last_name=last_name,
        email=email,
        salary=salary,
        join_date=date(2024, 6, 1),
        department_id=department.id,
        role_id=job_role.id,
        status="active",
    )
    db.add(employee)
    db.flush()
    return employee


def seed() -> None:
    db = SessionLocal()
    try:
        academics = get_or_create_department(db, "Academics", "Teaching staff department")
        admin_dept = get_or_create_department(db, "Administration", "School administration")
        teacher_role = get_or_create_job_role(db, "Teacher", "Teaching staff")
        admin_role = get_or_create_job_role(db, "Administrator", "School administrator")

        get_or_create_employee(
            db,
            first_name="Jane",
            last_name="Teacher",
            email="teacher@school.com",
            salary=30000,
            department=academics,
            job_role=teacher_role,
        )
        get_or_create_employee(
            db,
            first_name="John",
            last_name="Admin",
            email="admin@school.com",
            salary=50000,
            department=admin_dept,
            job_role=admin_role,
        )
        get_or_create_employee(
            db,
            first_name="Helen",
            last_name="HR",
            email="hr@school.com",
            salary=45000,
            department=admin_dept,
            job_role=admin_role,
        )

        get_or_create_user(db, "admin@school.com", "admin")
        get_or_create_user(db, "hr@school.com", "hr")
        get_or_create_user(db, "teacher@school.com", "employee")

        teacher = db.query(Employee).filter(Employee.email == "teacher@school.com").first()
        existing_attendance = (
            db.query(Attendance)
            .filter(
                Attendance.employee_id == teacher.id,
                Attendance.date == date(2026, 6, 1),
            )
            .first()
        )
        if not existing_attendance:
            db.add(
                Attendance(
                    employee_id=teacher.id,
                    date=date(2026, 6, 1),
                    status=AttendanceStatus.PRESENT,
                )
            )

        db.commit()
        print("Demo data seeded successfully.")
        print("Demo accounts (password change required on first login):")
        for email, password in DEMO_PASSWORDS.items():
            print(f"  {email} / {password}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
