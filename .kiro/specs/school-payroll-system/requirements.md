# Requirements Document

## Introduction

This document covers the phased completion of an AI Web-Based School Payroll Management System. The system is approximately 70% complete. The immediate goal is **Phase 1: Stabilization** — making the existing FastAPI/PostgreSQL backend fully stable, startup-clean, and production-ready. Subsequent phases (Late Coming Policy, Designations, Overtime, Academic Calendar, Frontend Polish, and AI features) are captured here to ensure the architecture decisions in Phase 1 do not block later work.

The backend uses FastAPI, SQLAlchemy 2.0, PostgreSQL, Alembic, JWT Auth, and Pydantic V2. The frontend uses React 19, Vite, Tailwind CSS v4, React Router, and Axios. Architecture follows a Service Layer pattern with a modular REST API.

---

## Glossary

- **System**: The School Payroll Management System as a whole.
- **Backend**: The FastAPI application served via `uvicorn app.main:app --reload`.
- **Database**: The PostgreSQL instance identified by `DATABASE_URL` in the `.env` file.
- **Alembic**: The database migration tool managing all schema changes.
- **Migration Chain**: The ordered sequence of Alembic revision files whose combined `upgrade()` functions produce the target schema.
- **ORM Model**: A SQLAlchemy `Base`-derived class in `app/models/`.
- **Schema**: The actual table and column definitions present in the PostgreSQL database at runtime.
- **Migration Head**: The latest applied Alembic revision as recorded in `alembic_version`.
- **Startup**: The process of executing `uvicorn app.main:app --reload` and reaching a running state with no unhandled exceptions.
- **Health Endpoint**: The `GET /health` route that reports `{"status": "ok", "database": "ok"}`.
- **Docs Endpoint**: The auto-generated OpenAPI UI at `/docs`.
- **Employee**: A person whose payroll and attendance are managed by the System.
- **HR**: A user with role `hr` who manages attendance, leave, and payroll data.
- **Admin**: A user with role `admin` who has all HR permissions plus user management.
- **Payroll Snapshot**: A persisted row in `payrolls` representing a computed monthly payroll for one Employee.
- **Daily Salary**: Base salary divided by the configured number of working days per month (default: 30).
- **Net Salary**: Base salary minus all deductions plus all bonuses and overtime pay.
- **Attendance Status**: One of `PRESENT`, `ABSENT`, `HALF_DAY`, `ON_LEAVE`, `LATE`.
- **Late Penalty Rule**: A row in `late_penalty_rules` defining the deduction applied when an Employee's late minutes fall within a specified range.
- **Designation**: A job title classification for Employees (Phase 2).
- **Overtime**: Extra hours worked beyond the standard shift, entered manually by HR (Phase 3).
- **Academic Calendar**: A schedule of working days, school holidays, exam holidays, and vacations (Phase 3).
- **Payslip PDF**: A downloadable PDF document summarising a monthly Payroll Snapshot for one Employee (Phase 3).

---

## Requirements

---

### Requirement 1: PostgreSQL Connection Verification

**User Story:** As an Admin, I want the System to verify its PostgreSQL connection on startup, so that database misconfiguration is detected immediately rather than at the first request.

#### Acceptance Criteria

1. WHEN the Backend starts, THE Backend SHALL execute a `SELECT 1` query against the Database during the ASGI lifespan startup event before any request handler is invoked.
2. IF the `SELECT 1` query raises an exception at startup, THEN THE Backend SHALL log an error message that includes the word `DATABASE_URL`, the resolved host, and the resolved port, and the process SHALL exit with a non-zero status code.
3. IF the `SELECT 1` query succeeds at startup, THEN THE Backend SHALL log a confirmation message and continue to accept incoming requests.
4. WHEN `GET /health` is called and the Database is reachable, THE Backend SHALL return HTTP 200 with body `{"status": "ok", "database": "ok"}`.
5. WHEN `GET /health` is called and the Database is NOT reachable, THE Backend SHALL return HTTP 200 with body `{"status": "degraded", "database": "error"}`.

---

### Requirement 2: Alembic Migration State Verification

**User Story:** As an Admin, I want the migration state to be verified before the Backend accepts traffic, so that the Schema always matches what the ORM Models expect.

#### Acceptance Criteria

1. WHEN the Backend starts, THE Backend SHALL read the `alembic_version` table to determine the current migration head applied to the Database.
2. IF the current migration head in the Database does not match the latest revision in the Migration Chain, THEN THE Backend SHALL log a warning that states the current head, the expected head, and the command `alembic upgrade head` needed to resolve the divergence, and SHALL refuse to start.
3. IF the current migration head in the Database matches the latest revision in the Migration Chain, THEN THE Backend SHALL proceed to accept traffic.
4. THE Alembic Migration Chain SHALL resolve to exactly one head revision (i.e., `alembic heads` returns exactly one revision with no branches).
5. WHEN `alembic upgrade head` is executed against a fresh Database with no `alembic_version` table, THE Migration Chain SHALL apply all revisions without error and produce a Schema in which every table and column defined in the ORM Models exists with a compatible type.
6. WHEN `alembic upgrade head` is executed against a Database already at the latest revision, THE tool SHALL execute zero DDL statements and exit with code 0.

---

### Requirement 3: ORM Model and Database Schema Alignment

**User Story:** As a developer, I want every ORM Model column, type, constraint, and index to match the actual Database Schema, so that SQLAlchemy does not raise mapping or query errors at runtime.

#### Acceptance Criteria

1. THE Backend SHALL register ORM Models for all tables: `roles`, `users`, `departments`, `employees`, `attendance`, `leaves`, `payrolls`, `audit_logs`, `late_penalty_rules` in the Alembic `env.py` target metadata so autogenerate can detect drift for all of them.
2. WHEN `alembic check` is executed against the Database, THE Alembic tool SHALL report zero pending autogenerate differences between the registered ORM Models and the Database Schema.
3. THE `employees` table SHALL contain a `reporting_time` column of type `TIME WITHOUT TIME ZONE NOT NULL` with a server default of `'09:30:00'`.
4. THE `attendance` table SHALL contain columns: `is_override BOOLEAN NOT NULL DEFAULT false`, `override_reason TEXT`, `overridden_by UUID`, `overridden_at TIMESTAMP WITH TIME ZONE`, and `check_in_time TIME WITHOUT TIME ZONE`.
5. THE `payrolls` table SHALL contain columns `total_absent INTEGER NOT NULL DEFAULT 0` and `total_half_days INTEGER NOT NULL DEFAULT 0`, and a unique constraint named `uq_payroll_employee_month` on `(employee_id, month)` where `month` is stored as a `VARCHAR(7)` in `YYYY-MM` format.
6. THE `audit_logs` table SHALL have a B-tree index on each of `actor_id`, `action`, and `entity_id`, and a foreign key constraint from `actor_id` to `users.id`.
7. THE `late_penalty_rules` table SHALL contain columns `id UUID PRIMARY KEY`, `late_days_min INTEGER NOT NULL`, `deduction_amount DOUBLE PRECISION NOT NULL`, and `label VARCHAR(100)`.
8. IF a column present in an ORM Model is absent from the Database Schema, THEN an Alembic migration SHALL be generated that adds the column using `ADD COLUMN` with no `DROP COLUMN` or `DROP TABLE` statements.

---

### Requirement 4: Backend Startup Without Errors

**User Story:** As a developer, I want `uvicorn app.main:app --reload` to start cleanly, so that I can develop and deploy the Backend without manual intervention.

#### Acceptance Criteria

1. WHEN `uvicorn app.main:app --reload` is executed with a reachable Database and a valid `.env`, THE Backend SHALL emit the `Application startup complete` log line within 30 seconds. Database connectivity failures logged during the lifespan startup event do not block this criterion if the process exits with a non-zero code (covered by Requirement 1).
2. THE Backend SHALL import all routers — `auth`, `users`, `departments`, `employees`, `attendance`, `payroll`, `leave`, `dashboard`, `audit_logs` — without raising any unhandled exception during module-level execution (including `ImportError`, `AttributeError`, `RuntimeError`, and `TypeError`).
3. THE Backend SHALL load `settings` from the `.env` file on startup. IF `SECRET_KEY` is absent from `.env` and has no default, THEN THE Backend SHALL raise a `ValidationError` before starting. All other settings (`DATABASE_URL`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `ALGORITHM`) SHALL fall back to their documented defaults if absent.
4. IF any router import raises an unhandled exception during module-level execution, THEN THE Backend SHALL surface the exception message, the fully qualified module path, and the line number in the startup log before exiting.
5. WHEN `GET /docs` is requested after a successful startup, THE Backend SHALL return HTTP 200 with the OpenAPI UI HTML, and the UI SHALL list routes from all 9 registered router groups: `/auth`, `/users`, `/departments`, `/employees`, `/attendance`, `/payroll`, `/leave`, `/dashboard`, `/audit-logs`.

---

### Requirement 5: Authentication Verification

**User Story:** As an Admin, I want to confirm that JWT login and RBAC work correctly after stabilization, so that all role-based access controls remain intact.

#### Acceptance Criteria

1. WHEN `POST /auth/login` is called with a valid `username` and `password`, THE Auth_Service SHALL return HTTP 200 with a JSON body containing `access_token` (a signed JWT string), `token_type` (value `"bearer"`), the authenticated user's `role`, and `must_change_password` (boolean).
2. IF `POST /auth/login` is called with a `username` that exists but an incorrect `password`, THEN THE Auth_Service SHALL return HTTP 401 with a generic error message that does not reveal whether the username or password was wrong.
3. WHEN a request includes a valid, non-expired JWT in the `Authorization: Bearer <token>` header on a protected endpoint, THE Auth_Service SHALL pass the request through to the endpoint handler and return the handler's response.
4. IF a request to a protected endpoint omits the `Authorization` header or provides a malformed token, THEN THE Auth_Service SHALL return HTTP 401 before invoking the endpoint handler.
5. IF a request to a protected endpoint includes a JWT whose expiry timestamp is in the past, THEN THE Auth_Service SHALL return HTTP 401.
6. IF a request is made to an endpoint that requires role `admin` or `hr` by a user with role `employee`, THEN THE Auth_Service SHALL return HTTP 403.
7. WHEN `GET /auth/me` is called with a valid JWT for a user with role `employee`, THE Auth_Service SHALL return a JSON body that includes `employee_id` (UUID of the linked employee record) and `must_change_password` (boolean). For users with roles other than `employee`, `employee_id` SHALL be `null`.

---

### Requirement 6: Employee CRUD Verification

**User Story:** As an HR user, I want Employee create, read, update, and delete operations to function correctly, so that employee records remain accurate.

#### Acceptance Criteria

1. WHEN `POST /employees` is called by a user with role `admin` or `hr` with a body containing all required fields (`name`, `email`, `department_id`, `base_salary`, `reporting_time`), THE Employee_Service SHALL persist the Employee to the Database and return HTTP 201 with the created record including the generated `id`.
2. IF `POST /employees` is called with an `email` that already exists in the `employees` table, THEN THE Employee_Service SHALL return HTTP 400 with an error message referencing the duplicate email.
3. WHEN `GET /employees/{id}` is called for an `id` that exists in the Database, THE Employee_Service SHALL return HTTP 200 with the full Employee record.
4. IF `GET /employees/{id}` is called for an `id` that does not exist in the Database, THEN THE Employee_Service SHALL return HTTP 404.
5. WHEN `PUT /employees/{id}` is called with a partial or full set of updatable fields, THE Employee_Service SHALL update only the fields present in the request body, leave all other fields unchanged, and return HTTP 200 with the updated record.
6. WHEN `DELETE /employees/{id}` is called by a user with role `admin` or `hr`, THE Employee_Service SHALL permanently remove the Employee record from the Database and return HTTP 204.
7. THE `employees` table SHALL enforce a unique constraint on `email` at the database level, causing a database integrity error if bypassed at the application level.

---

### Requirement 7: Department CRUD Verification

**User Story:** As an Admin, I want Department management to function correctly, so that Employees can be assigned to valid departments.

#### Acceptance Criteria

1. WHEN `POST /departments` is called with a `name` that does not exist (case-insensitive) in the `departments` table, THE Department_Service SHALL persist the Department and return HTTP 201 with the created record.
2. IF `POST /departments` is called with a `name` that already exists in the `departments` table (case-insensitive), THEN THE Department_Service SHALL return HTTP 400 with a duplicate-name error message.
3. WHEN `GET /departments` is called, THE Department_Service SHALL return HTTP 200 with a JSON array of all Department records. IF pagination query parameters `skip` and `limit` are provided, THE Department_Service SHALL apply them.
4. WHEN `DELETE /departments/{id}` is called for a Department that exists and has no Employees assigned to it, THE Department_Service SHALL permanently remove the Department and return HTTP 204.
5. IF `DELETE /departments/{id}` is called for a Department that has one or more Employees assigned to it, THEN THE Department_Service SHALL return HTTP 409 with a message stating the department is in use.
6. IF `DELETE /departments/{id}` is called for a Department `id` that does not exist, THEN THE Department_Service SHALL return HTTP 404.

---

### Requirement 8: Attendance Verification

**User Story:** As an HR user, I want attendance marking and monthly reporting to work correctly, so that payroll calculations are based on accurate attendance data.

#### Acceptance Criteria

1. WHEN `POST /attendance` is called with a valid `employee_id`, a `date` on or before today, and a `status` of `PRESENT`, `ABSENT`, `HALF_DAY`, or `LATE`, THE Attendance_Service SHALL create the attendance record and return HTTP 201 with the created record. The status `ON_LEAVE` SHALL NOT be accepted via this endpoint.
2. IF `POST /attendance` is called with a `date` that is in the future (after today's UTC date), THEN THE Attendance_Service SHALL return HTTP 400.
3. IF `POST /attendance` is called for an `employee_id` and `date` combination that already has an attendance record with status other than `ON_LEAVE`, THEN THE Attendance_Service SHALL return HTTP 409.
4. IF `POST /attendance` is called for an `employee_id` and `date` combination that already has an attendance record with status `ON_LEAVE`, THEN THE Attendance_Service SHALL update the existing record to the new status and return HTTP 200 with the updated record.
5. WHEN `PUT /attendance/{id}/override` is called by a user with role `admin` or `hr` with a `status` of `PRESENT`, `ABSENT`, `HALF_DAY`, or `LATE` and a non-blank `override_reason`, THE Attendance_Service SHALL update the record and set `is_override = true`, `override_reason`, `overridden_by` (actor's user id), and `overridden_at` (current UTC timestamp), then return HTTP 200.
6. IF `PUT /attendance/{id}/override` is called with `status` of `ON_LEAVE`, THEN THE Attendance_Service SHALL return HTTP 422.
7. IF `PUT /attendance/{id}/override` is called for an attendance `id` that does not exist, THEN THE Attendance_Service SHALL return HTTP 404.
8. WHEN `GET /attendance/{employee_id}?month=M&year=Y` is called for an existing Employee with `M` between 1 and 12 and `Y` ≥ 2000, THE Attendance_Service SHALL return HTTP 200 with all attendance records for that Employee in the given month and a summary object containing `total_present`, `total_absent`, and `total_half_days`.
9. IF `GET /attendance/{employee_id}` is called for an `employee_id` that does not exist, THEN THE Attendance_Service SHALL return HTTP 404.
10. WHEN a Leave request transitions to `APPROVED` status, THE Attendance_Service SHALL create or update attendance records for every calendar date in the leave period (inclusive) to status `ON_LEAVE`, skipping only dates where `is_override = true`.

---

### Requirement 9: Leave Management Verification

**User Story:** As an HR user, I want leave requests to be created, reviewed, and approved or rejected without errors, so that leave data feeds correctly into attendance and payroll.

#### Acceptance Criteria

1. WHEN `POST /leave` is called with a valid `employee_id`, a `leave_type` of `CASUAL`, `SICK`, `PAID`, or `UNPAID`, a `start_date`, and an `end_date` where `end_date` ≥ `start_date`, THE Leave_Service SHALL create a leave record with status `PENDING` and return HTTP 201.
2. IF `POST /leave` is called with `end_date` before `start_date`, or with a `leave_type` outside the allowed enum values, THEN THE Leave_Service SHALL return HTTP 422.
3. WHEN `PATCH /leave/{id}/approve` is called by a user with role `admin` or `hr` for a leave record in `PENDING` status, THE Leave_Service SHALL set status to `APPROVED`, record `approved_by` as the actor's user id, trigger attendance marking for each date in the leave period (skipping dates with `is_override = true`), and write an audit log entry — all within a single database transaction that rolls back entirely on any failure.
4. IF `PATCH /leave/{id}/approve` is called for a leave record that is NOT in `PENDING` status, THEN THE Leave_Service SHALL return HTTP 409.
5. WHEN `PATCH /leave/{id}/reject` is called by a user with role `admin` or `hr` for a leave record in `PENDING` status, THE Leave_Service SHALL set status to `REJECTED` and write an audit log entry within a single database transaction.
6. IF `PATCH /leave/{id}/reject` is called for a leave record that is NOT in `PENDING` status, THEN THE Leave_Service SHALL return HTTP 409.
7. IF `PATCH /leave/{id}/approve` or `PATCH /leave/{id}/reject` is called for a `leave_id` that does not exist, THEN THE Leave_Service SHALL return HTTP 404.

---

### Requirement 10: Payroll Engine Verification

**User Story:** As an HR user, I want to generate and recalculate payroll snapshots for Employees, so that net salaries are computed accurately from attendance data.

#### Acceptance Criteria

1. WHEN `POST /payroll/generate` is called with an `employee_id` that exists, a `month` between 1 and 12, and a `year` ≥ 2000, THE Payroll_Service SHALL create a Payroll Snapshot and return HTTP 201 with fields: `base_salary`, `total_present`, `total_absent`, `total_half_days`, `leave_deductions`, `absent_deductions`, `half_day_deductions`, `net_salary`, and `status` set to `"generated"`.
2. IF `POST /payroll/generate` is called with an `employee_id` that does not exist, THEN THE Payroll_Service SHALL return HTTP 404.
3. IF `POST /payroll/generate` is called for an Employee whose `base_salary` is zero or null, THEN THE Payroll_Service SHALL return HTTP 422 with an error stating that base salary must be a positive value.
4. THE Payroll_Service SHALL compute Daily Salary as `base_salary / 30` (float division, rounded to 2 decimal places).
5. THE Payroll_Service SHALL compute absent deductions as `total_absent × Daily_Salary` (rounded to 2 decimal places).
6. THE Payroll_Service SHALL compute half-day deductions as `total_half_days × Daily_Salary × 0.5` (rounded to 2 decimal places).
7. THE Payroll_Service SHALL compute Net Salary as `base_salary − absent_deductions − half_day_deductions` (rounded to 2 decimal places).
8. IF `POST /payroll/generate` is called for an `employee_id` and `(month, year)` combination that already has a Payroll Snapshot, THEN THE Payroll_Service SHALL return HTTP 409.
9. WHEN `PATCH /payroll/{employee_id}/recalculate?month=M&year=Y` is called, THE Payroll_Service SHALL re-read the current attendance records for that month, recompute all fields, update the existing Payroll Snapshot in place, set `status` to `"recalculated"`, and return HTTP 200 with the updated snapshot.
10. IF `PATCH /payroll/{employee_id}/recalculate` is called for a month/year with no existing Payroll Snapshot, THEN THE Payroll_Service SHALL return HTTP 404.
11. WHEN `GET /payroll/{employee_id}?month=M&year=Y` is called, THE Payroll_Service SHALL return HTTP 200 with the stored Payroll Snapshot including: `employee_id`, `month`, `year`, `base_salary`, `total_present`, `total_absent`, `total_half_days`, `absent_deductions`, `half_day_deductions`, `leave_deductions`, `net_salary`, and `status`.
12. IF `GET /payroll/{employee_id}?month=M&year=Y` is called and no Payroll Snapshot exists for that month/year, THEN THE Payroll_Service SHALL return HTTP 404.
13. IF `GET /payroll/{employee_id}` is called by a user with role `employee` whose `employee_id` does not match the requested `employee_id`, THEN THE Payroll_Service SHALL return HTTP 403.

---

### Requirement 11: Audit Log Verification

**User Story:** As an Admin, I want all sensitive mutations to produce audit log entries, so that every change can be traced to the actor who made it.

#### Acceptance Criteria

1. WHEN an attendance record is created via `POST /attendance`, THE Audit_Service SHALL create an audit log entry with `actor_id` (the requesting user's id), `action` = `"attendance.created"`, `entity_type` = `"attendance"`, and `entity_id` (the new attendance record's id), within the same database transaction as the attendance insert.
2. WHEN an attendance record is overridden via `PUT /attendance/{id}/override`, THE Audit_Service SHALL create an audit log entry with `action` = `"attendance.overridden"` and the same `actor_id`, `entity_type`, and `entity_id` fields, within the same transaction.
3. WHEN a leave request is approved via `PATCH /leave/{id}/approve`, THE Audit_Service SHALL create an audit log entry with `action` = `"leave.approved"`, `entity_type` = `"leave"`, and `entity_id` (the leave record's id), within the same transaction as the status update.
4. WHEN a leave request is rejected via `PATCH /leave/{id}/reject`, THE Audit_Service SHALL create an audit log entry with `action` = `"leave.rejected"` and the same `entity_type` and `entity_id` fields, within the same transaction.
5. IF the database transaction that includes an audit log write is rolled back, THEN THE audit log entry SHALL also be rolled back (no partial audit records).
6. WHEN `GET /audit-logs` is called by a user with role `admin`, THE Audit_Service SHALL return HTTP 200 with a JSON object containing `items` (array of audit log entries ordered by `created_at` descending), `total` (total count), `skip` (applied offset, default 0), and `limit` (applied page size, default 20, maximum 100).
7. IF `GET /audit-logs` is called by a user with role `hr` or `employee`, THEN THE Audit_Service SHALL return HTTP 403.
8. THE `audit_logs` table SHALL enforce a foreign key from `actor_id` to `users.id` at the database level, causing a referential integrity error if an audit log references a non-existent user.

---

### Requirement 12: Late Coming Policy (Phase 2)

**User Story:** As an HR user, I want to configure late penalty rules and have them applied during payroll generation, so that late arrivals result in correct deductions.

#### Acceptance Criteria

1. THE System SHALL maintain a `late_penalty_rules` table with columns `id UUID PRIMARY KEY`, `min_late_minutes INTEGER NOT NULL`, `max_late_minutes INTEGER`, `deduction_type VARCHAR(20) NOT NULL` (values: `"none"`, `"warning"`, `"half_day"`, `"full_day"`), and `label VARCHAR(100)`.
2. WHEN HR marks attendance with status `LATE` and a `check_in_time` value, THE Attendance_Service SHALL compute `late_minutes` as the integer number of minutes between the Employee's `reporting_time` and the recorded `check_in_time` (both as TIME values). IF `check_in_time` ≤ `reporting_time`, THEN `late_minutes` SHALL be recorded as 0.
3. WHEN `late_minutes` is between 0 and 10 inclusive, THE Payroll_Service SHALL apply zero monetary deduction for that attendance record.
4. WHEN `late_minutes` is between 11 and 30 inclusive, THE Payroll_Service SHALL record a `"warning"` flag on the Payroll Snapshot but apply zero monetary deduction for that attendance record.
5. WHEN `late_minutes` is between 31 and 60 inclusive, THE Payroll_Service SHALL apply a deduction of `Daily_Salary × 0.5` for that attendance record.
6. WHEN `late_minutes` exceeds 60, THE Payroll_Service SHALL apply a deduction of `Daily_Salary × 1.0` for that attendance record.
7. WHEN `POST /payroll/generate` is called, THE Payroll_Service SHALL sum all per-record late deductions for the month, store the total as `late_deductions` on the Payroll Snapshot, and subtract it from Net Salary.

---

### Requirement 13: Designation Management (Phase 2)

**User Story:** As an HR user, I want to assign a designation to each Employee, so that job titles are tracked alongside salary and department.

#### Acceptance Criteria

1. THE System SHALL maintain a `designations` table with columns `id UUID PRIMARY KEY`, `name VARCHAR(100) NOT NULL UNIQUE`, and `description TEXT`.
2. WHEN `POST /designations` is called with a `name` that does not already exist in the `designations` table (case-insensitive), THE Designation_Service SHALL persist the record and return HTTP 201 with the created Designation.
3. IF `POST /designations` is called with a `name` that already exists (case-insensitive), THEN THE Designation_Service SHALL return HTTP 409.
4. THE `employees` table SHALL contain a nullable `designation_id UUID` column with a foreign key constraint referencing `designations.id`.
5. WHEN `PUT /employees/{id}` is called with a `designation_id` that exists in the `designations` table, THE Employee_Service SHALL update the Employee's `designation_id` and return HTTP 200 with the updated record.
6. IF `PUT /employees/{id}` is called with a `designation_id` that does not exist in the `designations` table, THEN THE Employee_Service SHALL return HTTP 422.

---

### Requirement 14: Overtime Module (Phase 3)

**User Story:** As an HR user, I want to enter overtime hours for Employees, so that overtime pay is included in the monthly payroll.

#### Acceptance Criteria

1. THE System SHALL maintain an `overtime_records` table with columns `id UUID PRIMARY KEY`, `employee_id UUID NOT NULL` (FK → `employees.id`), `date DATE NOT NULL`, `hours DOUBLE PRECISION NOT NULL`, and `rate_multiplier DOUBLE PRECISION NOT NULL DEFAULT 1.5`.
2. WHEN `POST /overtime` is called with a valid `employee_id`, a `date` on or before today, and `hours` > 0, THE Overtime_Service SHALL persist the record and return HTTP 201.
3. IF `POST /overtime` is called with `hours` ≤ 0, THEN THE Overtime_Service SHALL return HTTP 422.
4. THE Payroll_Service SHALL compute overtime payment for each overtime record as `hours × Daily_Salary × rate_multiplier` (rounded to 2 decimal places).
5. WHEN `POST /payroll/generate` is called, THE Payroll_Service SHALL sum all overtime payments for the Employee in the given month, store the total as `overtime_pay` on the Payroll Snapshot, and add it to Net Salary.

---

### Requirement 15: Academic Calendar Integration (Phase 3)

**User Story:** As an Admin, I want to define school holidays and vacation periods, so that attendance and payroll calculations exclude non-working days automatically.

#### Acceptance Criteria

1. THE System SHALL maintain an `academic_calendar` table with columns `id UUID PRIMARY KEY`, `date DATE NOT NULL UNIQUE`, `day_type VARCHAR(50) NOT NULL`, and `description TEXT`.
2. THE `day_type` column SHALL accept only the values `WORKING_DAY`, `SCHOOL_HOLIDAY`, `EXAM_HOLIDAY`, and `VACATION`. Any other value SHALL be rejected with HTTP 422.
3. WHEN `POST /attendance` is called for a `date` that exists in `academic_calendar` with a `day_type` other than `WORKING_DAY`, THE Attendance_Service SHALL return HTTP 400 with an error message identifying the date and its day type.
4. WHEN `POST /payroll/generate` is called, IF the month/year has at least one `WORKING_DAY` entry in `academic_calendar`, THEN THE Payroll_Service SHALL use the count of `WORKING_DAY` dates in that month as `total_working_days` for Daily Salary computation instead of the default 30.
5. WHEN `POST /payroll/generate` is called for a month that has no entries in `academic_calendar`, THE Payroll_Service SHALL fall back to `total_working_days = 30`.

---

### Requirement 16: Payroll Reports and Payslip PDF (Phase 3)

**User Story:** As an HR user, I want to download a Payslip PDF for each Employee, so that salary details can be distributed in a formal document.

#### Acceptance Criteria

1. WHEN `GET /payroll/{employee_id}/payslip?month=M&year=Y` is called for an existing Payroll Snapshot, THE Payroll_Service SHALL generate and return a PDF file containing: employee full name, designation name, department name, month and year label, base salary, itemised allowances, itemised deductions (absent, half-day, late, leave), overtime pay, net salary, and the date the payslip was generated.
2. THE Payroll_Service SHALL set the HTTP response `Content-Type` header to `application/pdf` and include a `Content-Disposition: attachment; filename="payslip_{employee_id}_{YYYY-MM}.pdf"` header.
3. IF `GET /payroll/{employee_id}/payslip?month=M&year=Y` is called and no Payroll Snapshot exists for that month/year, THEN THE Payroll_Service SHALL return HTTP 404.
4. WHEN `GET /payroll/{employee_id}/history` is called, THE Payroll_Service SHALL return HTTP 200 with a JSON array of all Payroll Snapshots for that Employee ordered by `month` descending (most recent first).
5. IF `GET /payroll/{employee_id}/history` is called for an `employee_id` that does not exist, THEN THE Payroll_Service SHALL return HTTP 404.

---

### Requirement 17: Frontend Dashboard and Charts (Phase 4)

**User Story:** As an HR user, I want a polished dashboard with real-time statistics and charts, so that I can monitor payroll and attendance at a glance.

#### Acceptance Criteria

1. WHEN the Dashboard page is loaded by a user with role `admin` or `hr`, THE Dashboard_Service SHALL return HTTP 200 with: `total_employees` (integer), `monthly_payroll_total` (float for the current calendar month), `attendance_summary` (counts of PRESENT/ABSENT/HALF_DAY/LATE/ON_LEAVE for the current month), and `leave_statistics` (count of PENDING/APPROVED/REJECTED leaves for the current month).
2. THE Frontend SHALL render a bar chart displaying monthly payroll expenditure (`net_salary` sum) for the 12 most recent months in which at least one Payroll Snapshot exists.
3. THE Frontend SHALL render a pie or doughnut chart displaying the breakdown of attendance statuses (PRESENT, ABSENT, HALF_DAY, LATE, ON_LEAVE) for the current calendar month.
4. IF `GET /dashboard` returns an HTTP error or network failure, THEN THE Frontend SHALL display an inline error notice and continue rendering any previously loaded chart data rather than replacing the page with a full-screen error.

---

### Requirement 18: AI Features (Phase 5 — DO NOT BUILD BEFORE PHASE 5)

**User Story:** As an Admin, I want AI-powered analytics and forecasting, so that I can make data-driven payroll and staffing decisions.

#### Acceptance Criteria

1. WHERE the AI_Assistant feature flag is enabled in settings, THE AI_Service SHALL accept a natural-language query string and return a structured JSON response containing a human-readable answer and the underlying data points used to produce it.
2. WHERE the AI_Analytics feature flag is enabled, THE AI_Service SHALL generate a trend analysis report for payroll expenditure over a user-specified date range and return it as a structured JSON response.
3. WHERE the AI_Payroll_Forecasting feature flag is enabled, THE AI_Service SHALL predict the total payroll cost for the next calendar month based on the last 6 months of Payroll Snapshots and return the prediction with a confidence score.
4. WHERE the AI_Leave_Prediction feature flag is enabled, THE AI_Service SHALL estimate the probability that a specific Employee will take leave in the next 30 days based on that Employee's historical leave records and return the estimate as a float between 0.0 and 1.0.
5. THE Backend SHALL not import, initialise, or load any AI-related module, package, or dependency during Phase 1 through Phase 4. All AI code SHALL be isolated behind a feature flag that defaults to disabled.
