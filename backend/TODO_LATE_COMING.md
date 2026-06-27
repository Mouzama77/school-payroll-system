# TODO - LATE COMING POLICY (staged)

## Stage 1: Models
- [ ] Add `reporting_time` to `Employee` model (HH:MM, stored as Time or String)
- [ ] Add `check_in_time` to `Attendance` model (Time or String, nullable)
- [ ] Add `total_late_days` / `late_days`-related fields to payroll storage model as needed (or recompute from attendance)
- [ ] Create new `LatePenaltyRule` model: threshold (late_days_min) + deduction_amount
- [ ] Export all new models from `backend/app/models/__init__.py`

## Stage 2: Alembic migrations
- [ ] Create migration for Employee + Attendance new columns
- [ ] Create migration for `late_penalty_rules` table
- [ ] Create migration for payroll late fields

## Stage 3: Service wiring
- [ ] Update `AttendanceCreate` schema to accept `check_in_time`
- [ ] Update `AttendanceService.mark_attendance` to store `check_in_time`
- [ ] Update `AttendanceService.get_monthly_attendance` to count `total_late_days`
- [ ] Ensure attendance summary normalization is dict-based everywhere

## Stage 4: Payroll integration
- [ ] Update `AttendanceSummary` + `MonthlyAttendanceResponse.summary` schema to include `total_late_days`
- [ ] Update `core/payroll_rules.py` to compute late penalty using DB-driven `LatePenaltyRule` (single-tier => highest matching threshold)
- [ ] Update `payroll_service.py` to pass structured late inputs to core
- [ ] Update `Payroll` model + `PayrollResponse` schema + mapping to include `late_coming_deduction` separately

## Stage 5: Validation & tests
- [ ] Compile/import check
- [ ] Run pytest

