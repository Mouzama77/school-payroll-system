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
