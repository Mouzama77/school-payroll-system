# Implementation Tasks: School Payroll Management System

## Phase 1: Stabilization

### Task 1: Fix Alembic Migration Chain to Single Head
- [x] 1.1 Audit all files in `backend/alembic/versions/` and map the full revision DAG to identify any branch points
- [x] 1.2 Confirm `67b419aadb77_merge_leave_and_attendance_heads.py` is the single terminal merge; if any other branches exist, create an additional merge migration
- [x] 1.3 Verify `alembic heads` returns exactly one revision (Req 2.4)
- [x] 1.4 Run `alembic upgrade head` against a clean database and confirm all tables are created without error (Req 2.5)

### Task 2: Align ORM Models with Required Schema
- [ ] 2.1 Open `backend/app/models/employee.py` and add `reporting_time` column (`Time`, nullable=False, server_default='09:30:00') if absent (Req 3.3)
- [ ] 2.2 Open `backend/app/models/attendance.py` and add missing columns: `is_override` (Boolean, default=False, nullable=False), `override_reason` (Text, nullable=True), `overridden_by` (UUID FK→users.id, nullable=True), `overridden_at` (DateTime(timezone=True), nullable=True), `check_in_time` (Time, nullable=True) (Req 3.4)
- [ ] 2.3 Open `backend/app/models/payroll.py` and add `total_absent` (Integer, default=0, nullable=False), `total_half_days` (Integer, default=0, nullable=False); ensure `month` column is `String(7)` and `uq_payroll_employee_month` unique constraint exists on `(employee_id, month)` (Req 3.5)
- [ ] 2.4 Open `backend/app/models/audit_log.py` and add FK constraint `actor_id` → `users.id`; add B-tree indexes on `actor_id`, `action`, and `entity_id` (Req 3.6)
- [ ] 2.5 Open `backend/app/models/late_penalty_rule.py` (create if absent) with columns `id` (UUID PK), `late_days_min` (Integer, nullable=False), `deduction_amount` (Float/Double, nullable=False), `label` (String(100)) (Req 3.7)
- [ ] 2.6 Register all ORM models (`roles`, `users`, `departments`, `employees`, `attendance`, `leaves`, `payrolls`, `audit_logs`, `late_penalty_rules`) in `backend/alembic/env.py` `target_metadata` (Req 3.1)

### Task 3: Generate and Apply Schema Alignment Migrations
- [ ] 3.1 Run `alembic revision --autogenerate -m "align_schema_phase1"` and review the generated file — ensure it contains only `ADD COLUMN` / `CREATE INDEX` / `ADD CONSTRAINT` statements with no `DROP COLUMN` or `DROP TABLE` (Req 3.8)
- [ ] 3.2 Apply migration with `alembic upgrade head` and confirm success
- [ ] 3.3 Run `alembic check` and confirm zero pending differences (Req 3.2)

### Task 4: Implement ASGI Lifespan Startup Checks
- [ ] 4.1 In `backend/app/main.py`, implement an `@asynccontextmanager` lifespan that runs on startup:
  - Execute `SELECT 1` via the SQLAlchemy engine; on failure log error containing `DATABASE_URL`, host, and port, then `sys.exit(1)` (Req 1.1, 1.2, 1.3)
  - Read `alembic_version` table and compare against the script head from `alembic.config`; on mismatch log warning with current head, expected head, and `alembic upgrade head` command, then refuse to start (Req 2.1, 2.2, 2.3)
- [ ] 4.2 Pass the lifespan to the `FastAPI(lifespan=...)` constructor

### Task 5: Fix Health and Root Endpoints
- [ ] 5.1 In `backend/app/main.py` (or a dedicated router), ensure `GET /health` attempts a `SELECT 1` at request time and returns `{"status": "ok", "database": "ok"}` on success or `{"status": "degraded", "database": "error"}` on failure (Req 1.4, 1.5)
- [ ] 5.2 Ensure `GET /` returns `{"message": "School Payroll API is running"}`

### Task 6: Fix Settings and Config Module
- [ ] 6.1 In `backend/app/core/config.py`, confirm `SECRET_KEY` has no default value so Pydantic raises `ValidationError` when absent (Req 4.3)
- [ ] 6.2 Ensure `DATABASE_URL`, `ACCESS_TOKEN_EXPIRE_MINUTES`, and `ALGORITHM` have documented defaults (Req 4.3)
- [ ] 6.3 Ensure `CORS_ORIGINS` env var is parsed as a comma-separated list with default `http://localhost:5173`

### Task 7: Fix All Router Imports and Register All 9 Routers
- [ ] 7.1 In `backend/app/main.py`, ensure all 9 routers are imported and included: `auth`, `users`, `departments`, `employees`, `attendance`, `payroll`, `leave`, `dashboard`, `audit_logs` (Req 4.2, 4.5)
- [ ] 7.2 Fix any `ImportError`, `AttributeError`, or circular import in each router module by reading each file and resolving issues
- [ ] 7.3 Confirm `GET /docs` returns HTTP 200 listing all 9 route groups (Req 4.5)

### Task 8: Fix JWT Authentication and RBAC
- [ ] 8.1 In `backend/app/auth/jwt.py`, ensure `encode_token` produces a signed HS256 JWT with `sub`, `role`, and `exp` claims (Req 5.1)
- [ ] 8.2 In `backend/app/auth/dependencies.py`, ensure `get_current_user` returns HTTP 401 for missing/malformed/expired tokens (Req 5.3, 5.4, 5.5)
- [ ] 8.3 Ensure `require_roles` returns HTTP 403 when the authenticated user's role is not in the allowed set (Req 5.6)
- [ ] 8.4 In `backend/app/api/auth.py`, ensure `POST /auth/login` returns `access_token`, `token_type`, `role`, and `must_change_password`; returns HTTP 401 with a generic message on bad credentials (Req 5.1, 5.2)
- [ ] 8.5 Ensure `GET /auth/me` returns `employee_id` (UUID or null) and `must_change_password` (Req 5.7)

### Task 9: Fix Employee CRUD Service
- [ ] 9.1 In `backend/app/services/` and `backend/app/api/employees.py`, ensure `POST /employees` accepts `name`, `email`, `department_id`, `base_salary`, `reporting_time`, returns HTTP 201 with created record (Req 6.1)
- [ ] 9.2 Return HTTP 400 on duplicate `email` (Req 6.2)
- [ ] 9.3 Ensure `GET /employees/{id}` returns HTTP 200 with full record or HTTP 404 (Req 6.3, 6.4)
- [ ] 9.4 Ensure `PUT /employees/{id}` does partial update — only modifies fields present in the request body (Req 6.5)
- [ ] 9.5 Ensure `DELETE /employees/{id}` returns HTTP 204 (Req 6.6)
- [ ] 9.6 Confirm `employees.email` has a unique constraint in the ORM model and migration (Req 6.7)

### Task 10: Fix Department CRUD Service
- [ ] 10.1 Ensure `POST /departments` does case-insensitive duplicate check, returns HTTP 201 or HTTP 400 (Req 7.1, 7.2)
- [ ] 10.2 Ensure `GET /departments` returns HTTP 200 with array; apply `skip`/`limit` when provided (Req 7.3)
- [ ] 10.3 Ensure `DELETE /departments/{id}` returns HTTP 204 when no employees assigned, HTTP 409 when employees exist, HTTP 404 when not found (Req 7.4, 7.5, 7.6)

### Task 11: Fix Attendance Service
- [ ] 11.1 In `backend/app/schemas/attendance.py`, ensure `AttendanceCreate` enum excludes `ON_LEAVE` so Pydantic returns HTTP 422 if supplied (Req 8.1)
- [ ] 11.2 In `AttendanceService.mark_attendance`, validate date is not in the future (HTTP 400) (Req 8.2)
- [ ] 11.3 Return HTTP 409 if record exists with status other than `ON_LEAVE`; update and return HTTP 200 if status is `ON_LEAVE` (Req 8.3, 8.4)
- [ ] 11.4 In `AttendanceService.override_attendance`, set `is_override=True`, `override_reason`, `overridden_by`, `overridden_at` (UTC now); return HTTP 422 if new status is `ON_LEAVE`; return HTTP 404 if record not found (Req 8.5, 8.6, 8.7)
- [ ] 11.5 In `AttendanceService.get_monthly_attendance`, return records plus summary with `total_present`, `total_absent`, `total_half_days`; return HTTP 404 for unknown employee (Req 8.8, 8.9)
- [ ] 11.6 In leave approval flow, iterate date range and create/update attendance to `ON_LEAVE`, skipping records where `is_override=True` (Req 8.10)

### Task 12: Fix Leave Management Service
- [ ] 12.1 Ensure `POST /leave` accepts `CASUAL`, `SICK`, `PAID`, `UNPAID` leave types and `end_date >= start_date`; returns HTTP 201 with `PENDING` status (Req 9.1)
- [ ] 12.2 Return HTTP 422 for invalid leave_type or end_date < start_date (Req 9.2)
- [ ] 12.3 In `update_leave_status` for APPROVED: set status, record `approved_by`, trigger attendance ON_LEAVE marking, write audit log — all in one transaction; return HTTP 409 if not PENDING; HTTP 404 if not found (Req 9.3, 9.4, 9.7)
- [ ] 12.4 For REJECTED: set status, write audit log in one transaction; return HTTP 409 if not PENDING (Req 9.5, 9.6)

### Task 13: Fix Payroll Engine
- [ ] 13.1 In `PayrollService.generate_payroll`: validate employee exists (404), salary > 0 (422), no existing snapshot (409) (Req 10.1, 10.2, 10.3, 10.8)
- [ ] 13.2 Implement `_calculate_amounts`: `daily_salary = round(salary/30, 2)`, `absent_deductions = round(total_absent * daily_salary, 2)`, `half_day_deductions = round(total_half_days * daily_salary * 0.5, 2)`, `net_salary = round(salary - absent_deductions - half_day_deductions, 2)` (Req 10.4–10.7)
- [ ] 13.3 Persist snapshot with `status="generated"` and return HTTP 201 with all required fields (Req 10.1)
- [ ] 13.4 In `PayrollService.recalculate_payroll`: re-read attendance, recompute, update snapshot in place with `status="recalculated"`, return HTTP 200; return HTTP 404 if no existing snapshot (Req 10.9, 10.10)
- [ ] 13.5 In `PayrollService.get_payroll`: return snapshot with all fields or HTTP 404; enforce `assert_employee_access` so employee role can only access own payroll (403) (Req 10.11, 10.12, 10.13)

### Task 14: Fix Audit Log Service
- [ ] 14.1 In `AttendanceService.mark_attendance`, append `AuditLog(action="attendance.created", ...)` to the session before commit (Req 11.1)
- [ ] 14.2 In `AttendanceService.override_attendance`, append `AuditLog(action="attendance.overridden", ...)` before commit (Req 11.2)
- [ ] 14.3 In `update_leave_status` for APPROVED, append `AuditLog(action="leave.approved", ...)` (Req 11.3)
- [ ] 14.4 In `update_leave_status` for REJECTED, append `AuditLog(action="leave.rejected", ...)` (Req 11.4)
- [ ] 14.5 Ensure all audit writes are inside the same `db` session transaction so they roll back together (Req 11.5)
- [ ] 14.6 In `backend/app/api/audit_logs.py`, ensure `GET /audit-logs` returns paginated `{items, total, skip, limit}` sorted by `created_at DESC`; restrict to `admin` role only (Req 11.6, 11.7)

---

## Phase 2: Late Coming Policy and Designations

### Task 15: Late Penalty Rules — Schema and Migration
- [ ] 15.1 Update `late_penalty_rules` ORM model to include `min_late_minutes` (Integer, nullable=False), `max_late_minutes` (Integer, nullable=True), `deduction_type` (String(20), nullable=False — values: `"none"`, `"warning"`, `"half_day"`, `"full_day"`), `label` (String(100)) (Req 12.1)
- [ ] 15.2 Generate Alembic migration for `late_penalty_rules` schema change and apply it
- [ ] 15.3 Seed default tier rows via a data migration: 0–10 min → none, 11–30 min → warning, 31–60 min → half_day, >60 min → full_day

### Task 16: Late Minutes Computation in AttendanceService
- [ ] 16.1 When `POST /attendance` is called with `status=LATE` and `check_in_time` is provided, compute `late_minutes = max(0, floor((check_in_time - employee.reporting_time).total_seconds() / 60))` and store it (Req 12.2)
- [ ] 16.2 Persist `check_in_time` on the attendance record

### Task 17: Late Deductions in Payroll Generation
- [ ] 17.1 In `PayrollService.generate_payroll`, after computing absent/half-day deductions, fetch all LATE attendance records for the month that have a `check_in_time`
- [ ] 17.2 For each LATE record, look up the matching `late_penalty_rules` row by `late_minutes` range and apply: 0–10 → 0, 11–30 → 0 (warning flag), 31–60 → `daily_salary * 0.5`, >60 → `daily_salary * 1.0` (Req 12.3–12.6)
- [ ] 17.3 Sum all late deductions, store as `late_deductions` on the snapshot, subtract from `net_salary` (Req 12.7)

### Task 18: Designations — Schema, Migration, and CRUD
- [ ] 18.1 Create `backend/app/models/designation.py` with `Designation` model: `id` (UUID PK), `name` (String(100), unique, nullable=False), `description` (Text, nullable=True) (Req 13.1)
- [ ] 18.2 Add nullable `designation_id` UUID FK → `designations.id` column to `Employee` model (Req 13.4)
- [ ] 18.3 Generate and apply Alembic migration for both changes
- [ ] 18.4 Create `backend/app/api/designations.py` router with `POST /designations` (case-insensitive duplicate check → 409 or 201) and `GET /designations` (Req 13.2, 13.3)
- [ ] 18.5 Register the designations router in `backend/app/main.py`
- [ ] 18.6 In `PUT /employees/{id}`, handle `designation_id`: validate it exists in `designations` (422 if not, 200 with updated record if yes) (Req 13.5, 13.6)

---

## Phase 3: Overtime, Academic Calendar, and Payslip PDF

### Task 19: Overtime Module — Schema, Migration, and CRUD
- [ ] 19.1 Create `backend/app/models/overtime_record.py` with `OvertimeRecord` model: `id` (UUID PK), `employee_id` (UUID FK → employees.id, nullable=False), `date` (Date, nullable=False), `hours` (Float, nullable=False), `rate_multiplier` (Float, default=1.5, nullable=False) (Req 14.1)
- [ ] 19.2 Generate and apply Alembic migration
- [ ] 19.3 Create `backend/app/api/overtime.py` with `POST /overtime`: validate employee exists, date not in future, `hours > 0` (422 if ≤ 0), return HTTP 201 (Req 14.2, 14.3)
- [ ] 19.4 Register the overtime router in `backend/app/main.py`

### Task 20: Overtime Pay in Payroll Generation
- [ ] 20.1 In `PayrollService.generate_payroll`, after computing other amounts, fetch all `overtime_records` for the employee in the given month
- [ ] 20.2 Compute `overtime_pay = sum(round(r.hours * daily_salary * r.rate_multiplier, 2) for r in records)` (Req 14.4)
- [ ] 20.3 Store `overtime_pay` on the snapshot and add it to `net_salary` (Req 14.5)
- [ ] 20.4 Add `overtime_pay` column to `payrolls` ORM model and generate/apply migration

### Task 21: Academic Calendar — Schema, Migration, and CRUD
- [ ] 21.1 Create `backend/app/models/academic_calendar.py` with `AcademicCalendar` model: `id` (UUID PK), `date` (Date, unique, nullable=False), `day_type` (String(50), nullable=False), `description` (Text, nullable=True) (Req 15.1)
- [ ] 21.2 Add Pydantic validator in the schema that rejects `day_type` values outside `WORKING_DAY`, `SCHOOL_HOLIDAY`, `EXAM_HOLIDAY`, `VACATION` (HTTP 422) (Req 15.2)
- [ ] 21.3 Generate and apply Alembic migration
- [ ] 21.4 Create `backend/app/api/academic_calendar.py` with `POST /academic-calendar` and `GET /academic-calendar`; register in `main.py`

### Task 22: Academic Calendar Integration with Attendance and Payroll
- [ ] 22.1 In `AttendanceService.mark_attendance`, before creating the record look up the date in `academic_calendar`; if `day_type != WORKING_DAY`, return HTTP 400 with message identifying date and day type (Req 15.3)
- [ ] 22.2 In `PayrollService.generate_payroll`, count `WORKING_DAY` entries for the target month in `academic_calendar`; if count > 0 use it as `total_working_days` divisor instead of 30; else fall back to 30 (Req 15.4, 15.5)

### Task 23: Payslip PDF Generation
- [ ] 23.1 Add a PDF generation library to `backend/requirements.txt` (e.g., `reportlab` or `weasyprint`)
- [ ] 23.2 Create `backend/app/services/payslip_service.py` with a function that accepts a `PayrollSnapshot` + related employee/department/designation data and returns PDF bytes
- [ ] 23.3 The PDF must include: employee full name, designation name, department name, month/year label, base salary, itemised deductions (absent, half-day, late, leave), overtime pay, net salary, generation date (Req 16.1)
- [ ] 23.4 In `backend/app/api/payroll.py`, add `GET /payroll/{employee_id}/payslip?month=M&year=Y`:
  - Fetch snapshot (404 if not found)
  - Call `payslip_service.generate_pdf`
  - Return `StreamingResponse` with `Content-Type: application/pdf` and `Content-Disposition: attachment; filename="payslip_{employee_id}_{YYYY-MM}.pdf"` (Req 16.2)
  - Return HTTP 404 if snapshot not found, HTTP 403 if employee accessing another employee's payslip (Req 16.3 — see requirements)

---

## Cross-Cutting: Tests

### Task 24: Unit Tests for Payroll Calculation
- [ ] 24.1 Create `backend/tests/test_payroll_service.py`
- [ ] 24.2 Test `_calculate_amounts` with integer and float salaries to verify `daily_salary`, `absent_deductions`, `half_day_deductions`, `net_salary` are correctly rounded (Design Property 1, 2)
- [ ] 24.3 Test edge cases: 0 absences/half-days, all days absent, salary not divisible by 30

### Task 25: Unit Tests for Attendance State Machine
- [ ] 25.1 Create `backend/tests/test_attendance_service.py`
- [ ] 25.2 Test `mark_attendance` transitions: new record, ON_LEAVE override, duplicate non-leave → 409, future date → 400
- [ ] 25.3 Test `override_attendance`: sets all override fields, rejects ON_LEAVE status (422), 404 for missing record

### Task 26: Unit Tests for Leave Approval Flow
- [ ] 26.1 Create `backend/tests/test_leave_service.py`
- [ ] 26.2 Test that `update_leave_status(APPROVED)` creates ON_LEAVE attendance for each date in range, skips `is_override=True` dates, and writes one audit log entry
- [ ] 26.3 Test that a DB error rolls back both the leave status change and the audit log (Design Property 4, 5)

### Task 27: Integration Tests for Auth and RBAC
- [ ] 27.1 Create `backend/tests/test_auth.py`
- [ ] 27.2 Test `POST /auth/login` happy path, wrong password (401 with generic message), missing fields
- [ ] 27.3 Test protected endpoints: no token (401), expired token (401), wrong role (403), correct role (200)
