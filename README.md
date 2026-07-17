# School Payroll Management System

This project is organized into three main areas:

- `frontend/` — React + Tailwind client for payroll dashboards, employee management, and reports.
- `backend/` — FastAPI service that handles authentication, payroll calculations, and database access.
- `docs/` — Project documentation, architecture notes, and deployment guidance.

## Backend structure

- `backend/app/api/` — API routes and endpoints.
- `backend/app/core/` — configuration, settings, and shared app logic.
- `backend/app/db/` — database connection and migrations setup.
- `backend/app/models/` — SQLAlchemy models.
- `backend/app/schemas/` — Pydantic request/response schemas.
- `backend/app/services/` — business logic and external integrations.
- `backend/app/utils/` — helper functions and reusable utilities.
- `backend/tests/` — backend test suite.

## Frontend structure

- `frontend/src/components/` — reusable UI components.
- `frontend/src/pages/` — page-level views.
- `frontend/src/layouts/` — layout wrappers and shared page containers.
- `frontend/src/services/` — API client and network logic.
- `frontend/src/hooks/` — custom React hooks.
- `frontend/src/context/` — global state providers.
- `frontend/src/routes/` — routing configuration.
- `frontend/src/utils/` — frontend helper functions.
- `frontend/public/` — static assets.

## Forgot Password (OTP via email)

The password-reset flow uses a secure 6-digit one-time password (OTP)
delivered by email:

1. `POST /auth/forgot-password` `{ "email": "..." }` — generates a 6-digit
   OTP, stores only its bcrypt hash with a 10-minute expiry, and sends the
   email asynchronously via FastAPI `BackgroundTasks`. Always returns a
   generic message (no account enumeration). Rate limited per email.
2. `POST /auth/verify-otp` `{ "email": "...", "otp": "123456" }` — verifies
   the OTP (with attempt lockout) and returns a short-lived `reset_token`.
3. `POST /auth/reset-password-otp` `{ "email": "...", "reset_token": "...",
   "new_password": "..." }` — sets the new password. The token is single-use.

The frontend `Forgot Password` page (`/forgot-password`) walks the user
through all three steps (email → verify → reset).

### SMTP / email configuration

Configure these environment variables in `backend/.env` (see
`.env.example`):

| Variable | Purpose |
| --- | --- |
| `EMAIL_DEV_MODE` | `true` logs the OTP email to the console (no SMTP needed); set `false` to send real email. |
| `SMTP_HOST` / `SMTP_PORT` | SMTP server host and port (e.g. `smtp.gmail.com` / `587`). |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | SMTP credentials (for Gmail, use an App Password). |
| `SMTP_USE_TLS` / `SMTP_USE_SSL` | Transport security (STARTTLS on 587, SSL on 465). |
| `EMAIL_FROM` / `EMAIL_FROM_NAME` | Sender address and display name. |
| `OTP_LENGTH` | OTP digit count (default `6`). |
| `OTP_EXPIRE_MINUTES` | OTP lifetime (default `10`). |
| `OTP_MAX_ATTEMPTS` | Wrong-code attempts before lockout (default `5`). |
| `OTP_RESEND_COOLDOWN_SECONDS` | Minimum seconds between OTP requests (default `60`). |

Apply the database migration before first use:

```bash
cd backend
alembic upgrade head
```
