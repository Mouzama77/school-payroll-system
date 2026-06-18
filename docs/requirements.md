# Project Requirements

## Overview
This document outlines the functional and technical requirements for the School Payroll Management System.

## User Roles
- Super Admin
- HR/Admin
- Employee

## Modules
- Authentication
- Employee Management
- Department Management
- Attendance
- Leave Management
- Salary Structure
- Payroll Processing
- Payslip Generation
- Reports

## Functional Requirements

### Employee Management
- Register, update, and deactivate employee records.
- Store employee details such as name, role, department, salary grade, and bank information.
- Track employee status (active, inactive, resigned, on leave).

### Payroll Processing
- Calculate monthly salaries based on attendance, deductions, bonuses, and tax rules.
- Support overtime, allowances, and leave deductions.
- Generate payslips for employees.

### Attendance and Leave
- Record employee attendance.
- Track leave requests and approvals.
- Calculate payroll based on actual working days.

### Reports and Analytics
- Generate payroll summaries by department or month.
- Export reports to PDF or CSV.
- Provide dashboards for payroll trends and employee salary insights.

### Security and Access Control
- Secure authentication for admin, HR, and payroll staff.
- Role-based access control for sensitive payroll data.
- Audit logs for payroll changes and approvals.

## Configurable Payroll Rules

The system must allow administrators to configure payroll settings without code changes.

### Salary Components

Administrators can create and manage:

* Earnings (Basic Pay, HRA, Transport Allowance, Bonus, Incentives)
* Deductions (PF, ESI, Tax, Loan Recovery, Late Penalty)

Each component should support:

* Fixed amount
* Percentage-based calculation
* Formula-based calculation

### Attendance Rules

Administrators can configure:

* Working days per month
* Half-day rules
* Late arrival penalties
* Overtime rates

### Leave Rules

Administrators can configure:

* Leave types
* Annual leave balances
* Paid and unpaid leave
* Leave approval workflows

### Payroll Approval Workflow

The system should support:

* Payroll draft generation
* Review and approval by HR/Admin
* Payroll locking after approval
* Payslip release to employees


## Non-Functional Requirements
- System should support concurrent users.
- Data must be stored securely and backed up regularly.
- API responses should be fast and reliable.
- The application should be easy to maintain and extend.

## Technical Requirements
- Frontend: React + Tailwind CSS.
- Backend: FastAPI.
- Database: PostgreSQL.
- Environment configuration should use `.env` files.
- API endpoints should be documented and testable.
