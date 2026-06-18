# Core Database Schema

## roles

| Column      | Type        | Constraints      |
| ----------- | ----------- | ---------------- |
| id          | UUID        | Primary Key      |
| name        | VARCHAR(50) | Unique, Not Null |
| description | TEXT        | Nullable         |
| created_at  | TIMESTAMP   | Not Null         |

Examples:

* SUPER_ADMIN
* HR_ADMIN
* EMPLOYEE

---

## users

| Column        | Type         | Constraints            |
| ------------- | ------------ | ---------------------- |
| id            | UUID         | Primary Key            |
| email         | VARCHAR(255) | Unique, Not Null       |
| password_hash | TEXT         | Not Null               |
| role_id       | UUID         | Foreign Key → roles.id |
| is_active     | BOOLEAN      | Default TRUE           |
| last_login    | TIMESTAMP    | Nullable               |
| created_at    | TIMESTAMP    | Not Null               |
| updated_at    | TIMESTAMP    | Not Null               |

---

## departments

| Column      | Type         | Constraints      |
| ----------- | ------------ | ---------------- |
| id          | UUID         | Primary Key      |
| name        | VARCHAR(100) | Unique, Not Null |
| description | TEXT         | Nullable         |
| created_at  | TIMESTAMP    | Not Null         |

Examples:

* Mathematics
* Science
* Administration
* Accounts

---

## designations

| Column        | Type         | Constraints                  |
| ------------- | ------------ | ---------------------------- |
| id            | UUID         | Primary Key                  |
| title         | VARCHAR(100) | Not Null                     |
| department_id | UUID         | Foreign Key → departments.id |
| created_at    | TIMESTAMP    | Not Null                     |

Examples:

* Principal
* Teacher
* Accountant
* Clerk

---

## employees

| Column              | Type         | Constraints                   |
| ------------------- | ------------ | ----------------------------- |
| id                  | UUID         | Primary Key                   |
| employee_code       | VARCHAR(20)  | Unique, Not Null              |
| user_id             | UUID         | Foreign Key → users.id        |
| department_id       | UUID         | Foreign Key → departments.id  |
| designation_id      | UUID         | Foreign Key → designations.id |
| first_name          | VARCHAR(100) | Not Null                      |
| last_name           | VARCHAR(100) | Nullable                      |
| phone               | VARCHAR(20)  | Nullable                      |
| date_of_birth       | DATE         | Nullable                      |
| joining_date        | DATE         | Not Null                      |
| employment_type     | VARCHAR(50)  | Not Null                      |
| bank_account_number | TEXT         | Nullable                      |
| ifsc_code           | VARCHAR(20)  | Nullable                      |
| pan_number          | VARCHAR(20)  | Nullable                      |
| status              | VARCHAR(20)  | Default 'ACTIVE'              |
| created_at          | TIMESTAMP    | Not Null                      |
| updated_at          | TIMESTAMP    | Not Null                      |

Employment Types:

* Teaching
* Non-Teaching
* Contract

Status Values:

* ACTIVE
* INACTIVE
* RESIGNED
* ON_LEAVE
