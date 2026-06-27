# TODO - Production-ready payroll backend refactor

- [ ] Refactor `backend/app/services/payroll_service.py`:
  - [ ] Add temporary debug logging (use `logging`, remove `print`)
  - [ ] Add normalization helper for `attendance.summary` to dict format
  - [ ] Remove undefined `attendance` reference in `get_payroll()`
  - [ ] Add safe null handling for missing attendance/summary and missing salary
  - [ ] Standardize all summary access to dict keys
  - [ ] Add guarded try/except around payroll generation + recalculation to prevent silent crashes
- [ ] Only modify `backend/app/services/attendance_service.py` if summary format is found inconsistent (expected to already be correct)
- [x] Refactor `backend/app/services/payroll_service.py`:
  - [x] Add temporary debug logging (use `logging`, remove `print`)
  - [x] Add normalization helper for `attendance.summary` to dict format
  - [x] Remove undefined `attendance` reference in `get_payroll()`
  - [x] Add safe null handling for missing attendance/summary and missing salary
  - [x] Standardize all summary access to dict keys
  - [x] Add guarded try/except around payroll generation + recalculation to prevent silent crashes
- [x] Only modify `backend/app/services/attendance_service.py` if needed (no change required)
- [ ] Run `pytest` for backend tests
- [ ] Optionally run a quick import check / start app sanity command


