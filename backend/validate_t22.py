"""
Task 22 runtime validation.

22.1: mark_attendance on a non-WORKING_DAY date -> HTTP 400
22.2: generate_payroll uses WORKING_DAY count as divisor when defined;
      falls back to 30 when no academic calendar entries for the month.

Employee: 5d916a85-7a87-4049-9b18-dd0eb6684398
  salary = 1_200_000

Test month: 2026-02 (February 2026)
  Setup: Add 20 WORKING_DAY entries in Feb 2026
  => daily_salary = 1_200_000 / 20 = 60_000  (not 40_000)
  No absences => net_salary = 1_200_000

Fallback test: month=2026-06 (no calendar entries)
  => daily_salary = 1_200_000 / 30 = 40_000
"""
import uuid
from datetime import date

from app.db.session import SessionLocal
from app.models.academic_calendar import AcademicCalendar
from app.models.attendance import AttendanceStatus
from app.models.employee import Employee
from app.schemas.attendance import AttendanceCreate, AttendanceCreateStatus
from app.services.attendance_service import AttendanceService
from app.services.payroll_service import PayrollService
from fastapi import HTTPException

EID = uuid.UUID("5d916a85-7a87-4049-9b18-dd0eb6684398")
db = SessionLocal()

# ---- Setup: insert calendar entries for Feb 2026 ----
# 20 WORKING_DAY entries + 1 SCHOOL_HOLIDAY
working_days_feb = [date(2026, 2, d) for d in range(2, 22)]   # 2nd to 21st = 20 days
holiday = date(2026, 2, 1)   # Sunday / holiday

for d in working_days_feb:
    entry = db.query(AcademicCalendar).filter(AcademicCalendar.date == d).first()
    if not entry:
        db.add(AcademicCalendar(date=d, day_type="WORKING_DAY"))
holiday_entry = db.query(AcademicCalendar).filter(AcademicCalendar.date == holiday).first()
if not holiday_entry:
    db.add(AcademicCalendar(date=holiday, day_type="SCHOOL_HOLIDAY", description="Holiday"))
db.commit()
print(f"Setup: {len(working_days_feb)} WORKING_DAY entries + 1 SCHOOL_HOLIDAY in Feb 2026")

# ---- 22.1: POST attendance on SCHOOL_HOLIDAY -> HTTPException 400 ----
try:
    payload = AttendanceCreate(
        employee_id=EID,
        date=holiday,
        status=AttendanceCreateStatus.PRESENT,
    )
    # Get actor_id from DB
    from app.models.user import User
    admin = db.query(User).filter(User.role == "admin").first()
    AttendanceService.mark_attendance(db, payload, actor_id=admin.id)
    print("22.1 FAIL: should have raised HTTPException 400")
except HTTPException as e:
    assert e.status_code == 400, f"Expected 400, got {e.status_code}"
    assert "SCHOOL_HOLIDAY" in e.detail, f"Expected day_type in detail: {e.detail}"
    print(f"22.1 PASS: attendance on SCHOOL_HOLIDAY -> 400 '{e.detail}' ✓")
except Exception as e:
    print(f"22.1 ERROR: {e}")

# ---- 22.2a: generate_payroll for Feb 2026 -> uses 20 working days ----
# Expected: daily_salary = 1_200_000 / 20 = 60_000
p = PayrollService.generate_payroll(db=db, employee_id=EID, month=2, year=2026)
print(f"\n22.2a generate (Feb 2026, 20 WORKING_DAYs):")
print(f"  total_working_days = {p.total_working_days}")   # expected 20
print(f"  daily_salary       = {p.daily_salary}")          # expected 60_000
print(f"  net_salary         = {p.net_salary}")             # expected 1_200_000
assert p.total_working_days == 20, f"Expected 20, got {p.total_working_days}"
assert p.daily_salary == 60000.0, f"Expected 60000, got {p.daily_salary}"
assert p.net_salary == 1200000.0, f"Expected 1200000, got {p.net_salary}"
print("22.2a PASS: working_days=20, daily_salary=60000, net_salary=1200000 ✓")

# ---- 22.2b: generate_payroll for June 2026 (no calendar entries) -> fallback 30 ----
# Expected: daily_salary = 1_200_000 / 30 = 40_000
p2 = PayrollService.generate_payroll(db=db, employee_id=EID, month=6, year=2026)
print(f"\n22.2b generate (Jun 2026, no calendar entries, fallback):")
print(f"  total_working_days = {p2.total_working_days}")   # expected 30
print(f"  daily_salary       = {p2.daily_salary}")          # expected 40_000
assert p2.total_working_days == 30, f"Expected 30, got {p2.total_working_days}"
assert p2.daily_salary == 40000.0, f"Expected 40000, got {p2.daily_salary}"
print("22.2b PASS: fallback working_days=30, daily_salary=40000 ✓")

db.close()
print("\n✅ All Task 22 acceptance criteria passed.")
