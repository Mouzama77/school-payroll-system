# Requirements Document

## Introduction

This feature audits and enforces role-based access control (RBAC) across the school payroll system for three roles: **admin**, **hr**, and **employee**. The system already has partial RBAC infrastructure (JWT role claims, `require_roles` dependency, `RoleRoute`, and `permissions.js`). This spec formalises the complete access matrix, identifies gaps in enforcement, and establishes consistent rules for both the frontend (sidebar visibility and route guards) and the backend (API endpoint protection). No database schema changes and no new authentication mechanisms are introduced.

### Access Matrix

| Module / Route            | admin | hr  | employee |
|---------------------------|-------|-----|----------|
| Dashboard                 | ✓     | ✓   | ✓        |
| My Profile                | ✓     | –   | ✓        |
| My Attendance             | ✓     | –   | ✓        |
| My Payroll                | ✓     | –   | ✓        |
| My Leaves                 | ✓     | –   | ✓        |
| Employee Management       | ✓     | ✓   | –        |
| Attendance Management     | ✓     | ✓   | –        |
| Payroll Management        | ✓     | ✓   | –        |
| Leave Approval            | ✓     | ✓   | –        |
| Departments               | ✓     | –   | –        |
| Reports                   | ✓     | –   | –        |
| Settings                  | ✓     | –   | –        |
| User Management           | ✓     | –   | –        |

---

## Glossary

- **RBAC_System**: The role-based access control layer spanning both frontend and backend of the school payroll application.
- **Role**: A string value embedded in the JWT access token (`"admin"`, `"hr"`, or `"employee"`) that determines what a user may access.
- **JWT**: A signed JSON Web Token issued at login; its `role` claim is the single source of truth for the user's role.
- **ProtectedRoute**: A React component that redirects unauthenticated users to `/login`.
- **RoleRoute**: A React component that wraps a page route, reads the current user's role from `AuthContext`, and redirects unauthorised users to `/403`.
- **Sidebar**: The navigation panel rendered by `SidebarLayout` that lists links to application modules.
- **ROUTE_PERMISSIONS**: The `permissions.js` configuration object that maps each route key to the list of roles allowed to access it.
- **require_roles**: A FastAPI dependency factory that accepts a set of allowed role strings and raises HTTP 403 when the authenticated user's role is not in that set.
- **Management_Endpoint**: Any backend API endpoint that modifies or aggregates data belonging to multiple employees (create/update/delete employees, generate payroll, manage attendance, approve leaves, manage users).
- **Self_Endpoint**: Any backend API endpoint that returns data scoped to the requesting user's own employee record.
- **Forbidden_Page**: The `/403` page displayed when a user attempts to access a route their role does not permit.
- **Access_Token**: The JWT returned by the `/auth/login` endpoint and stored in `localStorage`.

---

## Requirements

### Requirement 1: Role-Driven Sidebar Visibility

**User Story:** As a user, I want the sidebar to show only the navigation items my role is permitted to access, so that I am not confused by links that would result in a 403 error.

#### Acceptance Criteria

1. IF a user is authenticated with role `employee`, THEN THE Sidebar SHALL display only: Dashboard, My Profile, My Attendance, My Payroll, and My Leaves.
2. IF a user is authenticated with role `hr`, THEN THE Sidebar SHALL display only: Dashboard, Employee Management, Attendance Management, Payroll Management, and Leave Approval.
3. IF a user is authenticated with role `admin`, THEN THE Sidebar SHALL display all navigation items defined in `ROUTE_PERMISSIONS`.
4. THE Sidebar SHALL derive visible items exclusively from `getNavigationForRole(role)` and SHALL NOT render any navigation link whose permission key is absent from the authenticated user's allowed set.
5. WHEN the `role` value in `AuthContext` changes, THE Sidebar SHALL re-evaluate and re-render only the navigation items permitted for the new role value.
6. IF the `role` value in `AuthContext` is `null`, `undefined`, or any value other than `"admin"`, `"hr"`, or `"employee"`, THEN `getNavigationForRole` SHALL return an empty array and THE Sidebar SHALL render no navigation links.

---

### Requirement 2: Frontend Route Guards

**User Story:** As a system, I want every application route to enforce the permitted roles before rendering a page, so that navigating directly to a URL does not bypass access control.

#### Acceptance Criteria

1. WHEN an unauthenticated user navigates to any protected route, THE RoleRoute SHALL redirect the user to `/login` using `replace` navigation.
2. WHEN an authenticated user navigates to a route whose `allowedRoles` list in `ROUTE_PERMISSIONS` does not include the user's role, THE RoleRoute SHALL redirect the user to `/403` using `replace` navigation.
3. THE RBAC_System SHALL wrap every module route listed in the access matrix with a `RoleRoute` component that specifies the correct `allowedRoles` sourced from `ROUTE_PERMISSIONS`.
4. WHEN a user with role `employee` navigates directly to `/users`, `/employees`, `/attendance`, `/payroll`, `/leaves`, `/departments`, `/reports`, or `/settings`, THE RoleRoute SHALL redirect the user to `/403`.
5. WHEN a user with role `hr` navigates directly to `/users`, `/departments`, `/reports`, or `/settings`, THE RoleRoute SHALL redirect the user to `/403`.
6. WHEN an unauthenticated user navigates to `/403` or `/change-password`, THE ProtectedRoute SHALL redirect the user to `/login` using `replace` navigation.
7. IF the `ROUTE_PERMISSIONS` entry for a given route key is `undefined`, `null`, or an empty array, THEN THE RoleRoute SHALL treat all roles as unauthorised and redirect to `/403`.

---

### Requirement 3: ProtectedRoute Component Contract

**User Story:** As a developer, I want a single reusable `ProtectedRoute` component that enforces authentication, so that I can wrap any route without duplicating authentication logic.

#### Acceptance Criteria

1. THE ProtectedRoute SHALL accept a `children` prop and render it only when `isAuthenticated` is `true` in `AuthContext`.
2. WHEN `isAuthenticated` is `false`, THE ProtectedRoute SHALL redirect the user to `/login` using `replace` navigation to prevent back-button bypass.
3. THE ProtectedRoute SHALL not perform role checking; role enforcement is the sole responsibility of `RoleRoute`.
4. WHEN `isAuthenticated` in `AuthContext` transitions from `true` to `false`, THE ProtectedRoute SHALL redirect the user to `/login` on the next render cycle without requiring an additional user action.
5. THE RBAC_System SHALL compose `ProtectedRoute` as the outer wrapper around `RoleRoute`, ensuring authentication is verified before role is evaluated.
6. WHEN `isAuthenticated` is `true` and `children` is rendered, THE ProtectedRoute SHALL pass all props through to `children` without modification.

---

### Requirement 4: HR Role Cannot Access User Management

**User Story:** As an admin, I want to ensure HR staff cannot access User Management, so that only administrators can create, modify, or delete system user accounts.

#### Acceptance Criteria

1. WHEN a user with role `hr` navigates to `/users`, THE RoleRoute SHALL redirect the user to `/403`.
2. THE ROUTE_PERMISSIONS configuration for the `users` key SHALL contain exactly `["admin"]` in its allowed roles array, and SHALL NOT include `"hr"` or `"employee"`.
3. IF a user with role `hr` is authenticated, THEN THE Sidebar SHALL not render the "User Management" navigation link.
4. WHEN a user with role `hr` sends a `GET /users` request to the backend API, THE require_roles dependency SHALL return HTTP 403 with an error message indicating insufficient permissions.
5. WHEN a user with role `hr` sends a `DELETE /users/{user_id}` request, THE require_roles dependency SHALL return HTTP 403 with an error message indicating insufficient permissions.
6. WHEN a user with role `hr` sends a `PUT /users/{user_id}` request, THE require_roles dependency SHALL return HTTP 403 with an error message indicating insufficient permissions.
7. WHEN a user with role `hr` sends a `POST /users` request, THE require_roles dependency SHALL return HTTP 403 with an error message indicating insufficient permissions.
8. WHEN a user with role `hr` sends a `PUT /users/{user_id}/password` request, THE require_roles dependency SHALL return HTTP 403 with an error message indicating insufficient permissions.

---

### Requirement 5: Employee Role Cannot Access Management Pages

**User Story:** As an admin, I want to ensure employees cannot access any management module, so that sensitive payroll, attendance, and HR data remains restricted.

#### Acceptance Criteria

1. WHEN a valid authenticated request from a user with role `employee` is made to `POST /employees/`, THE require_roles dependency SHALL return HTTP 403 with an error message indicating insufficient permissions.
2. WHEN a valid authenticated request from a user with role `employee` is made to `PUT /employees/{employee_id}` for any employee ID (including their own), THE require_roles dependency SHALL return HTTP 403 with an error message indicating insufficient permissions.
3. WHEN a valid authenticated request from a user with role `employee` is made to `DELETE /employees/{employee_id}`, THE require_roles dependency SHALL return HTTP 403 with an error message indicating insufficient permissions.
4. WHEN a valid authenticated request from a user with role `employee` is made to `POST /attendance/`, THE require_roles dependency SHALL return HTTP 403 with an error message indicating insufficient permissions.
5. WHEN a valid authenticated request from a user with role `employee` is made to `POST /payroll/generate`, THE require_roles dependency SHALL return HTTP 403 with an error message indicating insufficient permissions.
6. WHEN a valid authenticated request from a user with role `employee` is made to `GET /leaves/` (all leaves endpoint), THE require_roles dependency SHALL return HTTP 403 with an error message indicating insufficient permissions.
7. WHEN a valid authenticated request from a user with role `employee` is made to `PUT /leaves/{leave_id}` (approve/reject), THE require_roles dependency SHALL return HTTP 403 with an error message indicating insufficient permissions.

---

### Requirement 6: Employee Self-Service Data Scoping

**User Story:** As an employee, I want to access only my own attendance, payroll, and leave records, so that my personal data is private and other employees' data is not exposed.

#### Acceptance Criteria

1. WHEN a user with role `employee` sends a `GET /attendance/{employee_id}` request where `employee_id` does not match the `employee_id` linked to the requesting user's account, THE RBAC_System SHALL return HTTP 403.
2. WHEN a user with role `employee` sends a `GET /attendance/{employee_id}` request where `employee_id` matches the `employee_id` linked to the requesting user's account, THE RBAC_System SHALL return HTTP 200 with the attendance records for that employee.
3. WHEN a user with role `employee` sends a `GET /payroll/{employee_id}` request where `employee_id` does not match the `employee_id` linked to the requesting user's account, THE RBAC_System SHALL return HTTP 403.
4. WHEN a user with role `employee` sends a `GET /payroll/{employee_id}` request where `employee_id` matches the `employee_id` linked to the requesting user's account, THE RBAC_System SHALL return HTTP 200 with the payroll records for that employee.
5. WHEN a user with role `employee` sends a `GET /employees/` request, THE RBAC_System SHALL return HTTP 200 with a single-element array containing only the employee record linked to the requesting user.
6. WHEN a user with role `employee` sends a `GET /employees/{employee_id}` request where `employee_id` does not match the `employee_id` linked to the requesting user's account, THE RBAC_System SHALL return HTTP 403.
7. WHEN a user with role `employee` sends a `GET /leaves/my` request, THE RBAC_System SHALL return HTTP 200 with only the leave records whose `employee_id` matches the `employee_id` linked to the requesting user.
8. IF a user with role `employee` has no `employee_id` linked to their account, THEN THE RBAC_System SHALL return HTTP 404 for any of the self-service endpoints (`GET /attendance/{employee_id}`, `GET /payroll/{employee_id}`, `GET /employees/`, `GET /employees/{employee_id}`, `GET /leaves/my`), and this 404 SHALL take precedence over any 403 check.

---

### Requirement 7: JWT Role Claim as Single Source of Truth

**User Story:** As a developer, I want the frontend and backend to derive role information exclusively from the JWT, so that no secondary role store can cause inconsistency.

#### Acceptance Criteria

1. THE RBAC_System SHALL read the user's role solely from the `role` field in the JWT payload decoded by `decode_access_token`; IF the `role` field is absent from the JWT payload, THE RBAC_System SHALL return HTTP 401.
2. THE RBAC_System SHALL NOT introduce new authentication mechanisms, additional role tables, or middleware outside the existing `require_roles` dependency pattern.
3. WHEN a JWT token is expired, THE RBAC_System SHALL treat the user as unauthenticated: the backend SHALL return HTTP 401 for all protected requests, and the frontend `AuthContext` SHALL clear the stored role and set `isAuthenticated` to `false`.
4. THE `AuthContext` SHALL expose the `role` value equal to the value returned by `/auth/me` at login time; the `role` value in `AuthContext` SHALL NOT be mutated in memory or via storage after login without a new `/auth/me` call.
5. WHEN a valid JWT contains a `role` value that is not one of `"admin"`, `"hr"`, or `"employee"`, THE RBAC_System SHALL reject the request with HTTP 403.

---

### Requirement 8: Forbidden Page and User Feedback

**User Story:** As a user, I want to see a clear, role-appropriate message when I am denied access, so that I understand why I cannot view the requested page.

#### Acceptance Criteria

1. WHEN a user is redirected to `/403`, THE Forbidden_Page SHALL display visible plain-language text indicating that the user does not have permission to access the requested resource (without a raw error code or empty state as the sole output).
2. THE Forbidden_Page SHALL provide a navigation link that returns the user to `/dashboard`, which is the shared home route for all roles (`"admin"`, `"hr"`, and `"employee"`).
3. WHEN an unauthenticated user navigates to `/403`, THE ProtectedRoute SHALL redirect the user to `/login` using `replace` navigation.
4. THE Forbidden_Page SHALL display the user's current role as the exact JWT role string (`"admin"`, `"hr"`, or `"employee"`) so the user understands the context of the denial.

---

### Requirement 9: Permissions Configuration Completeness

**User Story:** As a developer, I want the `ROUTE_PERMISSIONS` configuration to be the single authoritative source for all route-to-role mappings, so that frontend and backend are consistently aligned.

#### Acceptance Criteria

1. THE ROUTE_PERMISSIONS object SHALL contain an entry for exactly these 13 route keys: `dashboard`, `profile`, `myAttendance`, `myPayroll`, `myLeaves`, `employees`, `attendance`, `payroll`, `leaves`, `users`, `departments`, `reports`, and `settings`.
2. THE ROUTE_PERMISSIONS entry for `profile`, `myAttendance`, `myPayroll`, and `myLeaves` SHALL contain exactly `["admin", "employee"]` and SHALL NOT include `"hr"`.
3. THE ROUTE_PERMISSIONS entry for `employees`, `attendance`, `payroll`, and `leaves` SHALL contain exactly `["admin", "hr"]` and SHALL NOT include `"employee"`.
4. THE ROUTE_PERMISSIONS entry for `users`, `departments`, `reports`, and `settings` SHALL contain exactly `["admin"]` and SHALL NOT include `"hr"` or `"employee"`.
5. THE ROUTE_PERMISSIONS entry for `dashboard` SHALL contain exactly `["admin", "hr", "employee"]`.
6. IF a route key is not present in `ROUTE_PERMISSIONS` or its value is `undefined`, `null`, or an empty array, THEN THE RoleRoute SHALL treat all roles as unauthorised and redirect to `/403`, consistent with Requirement 2 criterion 7.
