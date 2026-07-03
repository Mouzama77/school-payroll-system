from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    assert_employee_access,
    get_current_user,
    require_roles,
)
from app.auth.roles import MANAGEMENT_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.payroll import PayrollGenerateRequest, PayrollResponse
from app.services.payroll_service import PayrollService

router = APIRouter()


@router.post(
    "/generate",
    response_model=PayrollResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_payroll(
    payload: PayrollGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
):
    return PayrollService.generate_payroll(
        db=db,
        employee_id=payload.employee_id,
        month=payload.month,
        year=payload.year,
    )


@router.patch(
    "/{employee_id}/recalculate",
    response_model=PayrollResponse,
    summary="Recalculate payroll using current attendance data (HR/Admin only)",
)
def recalculate_payroll(
    employee_id: UUID,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
):
    """Recalculate an existing payroll snapshot after attendance overrides.

    Re-reads attendance records (which reflect any manual overrides) and
    updates the stored payroll figures in place. Requires payroll to have
    been generated first via POST /payroll/generate.
    """
    return PayrollService.recalculate_payroll(
        db=db,
        employee_id=employee_id,
        month=month,
        year=year,
    )


@router.get("/{employee_id}", response_model=PayrollResponse)
def get_payroll(
    employee_id: UUID,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assert_employee_access(db, current_user, employee_id)
    return PayrollService.get_payroll(
        db=db,
        employee_id=employee_id,
        month=month,
        year=year,
    )


@router.get("/{employee_id}/payslip")
def download_payslip(
    employee_id: UUID,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and return a payslip PDF for the given employee/month/year.

    Req 16.1: PDF includes employee name, designation, department, month/year,
              base salary, itemised deductions, overtime pay, net salary, generation date.
    Req 16.2: Content-Type: application/pdf; Content-Disposition attachment.
    Req 16.3 (implicit): employee role may only access their own payslip.
    """
    assert_employee_access(db, current_user, employee_id)

    from app.models.employee import Employee
    from app.models.department import Department
    from app.models.designation import Designation
    from app.services.payslip_service import generate_payslip_pdf
    from fastapi import HTTPException

    # Fetch snapshot (404 if not found)
    payroll_resp = PayrollService.get_payroll(
        db=db, employee_id=employee_id, month=month, year=year
    )

    # Fetch employee details
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    dept = db.query(Department).filter(Department.id == employee.department_id).first()
    desig = (
        db.query(Designation).filter(Designation.id == employee.designation_id).first()
        if employee.designation_id else None
    )

    full_name = f"{employee.first_name} {employee.last_name}"
    designation_name = desig.name if desig else None
    department_name = dept.name if dept else None

    pdf_bytes = generate_payslip_pdf(
        employee_full_name=full_name,
        designation_name=designation_name,
        department_name=department_name,
        month=payroll_resp.month,
        year=payroll_resp.year,
        base_salary=payroll_resp.base_salary,
        absent_deductions=payroll_resp.absent_deductions,
        half_day_deductions=payroll_resp.half_day_deductions,
        late_deductions=payroll_resp.late_deductions,
        leave_deductions=payroll_resp.leave_deductions,
        overtime_pay=payroll_resp.overtime_pay,
        net_salary=payroll_resp.net_salary,
    )

    month_str = f"{year:04d}-{month:02d}"
    filename = f"payslip_{employee_id}_{month_str}.pdf"

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )
