# Deployment Checklist

## Backend

- [ ] Copy `.env.example` to `backend/.env` and set production values
- [ ] Set a strong `SECRET_KEY` (32+ random characters)
- [ ] Set `DEBUG=false` and `APP_ENV=production`
- [ ] Configure production `DATABASE_URL`
- [ ] Set `CORS_ORIGINS` to your frontend domain only
- [ ] Set `FRONTEND_URL` to your deployed frontend URL
- [ ] Run migrations: `cd backend && alembic upgrade head`
- [ ] Seed demo data (optional): `python -m scripts.seed_demo_data`
- [ ] Start API with a production server (e.g. gunicorn + uvicorn workers)
- [ ] Verify `GET /health` returns database `ok`

## Frontend

- [ ] Copy `frontend/.env.example` to `frontend/.env`
- [ ] Set `VITE_API_BASE_URL` to your production API URL
- [ ] Build: `cd frontend && npm install && npm run build`
- [ ] Serve `frontend/dist` via nginx, Vercel, Netlify, or similar

## Security

- [ ] Change all demo passwords after first login
- [ ] Restrict database access to application server only
- [ ] Enable HTTPS on both frontend and backend
- [ ] Review RBAC rules for admin/hr/employee accounts
- [ ] Rotate `SECRET_KEY` if compromised

## Demo Accounts

| Email | Role | Default Password |
|-------|------|------------------|
| admin@school.com | admin | Admin@2026! |
| hr@school.com | hr | Hr@2026! |
| teacher@school.com | employee | Teacher@2026! |

All demo accounts require password change on first login (`must_change_password=true`).

## Smoke Tests

- [ ] Login as admin, hr, and employee
- [ ] Employee cannot access `/users`, `/departments`, management attendance/payroll pages
- [ ] HR can manage employees, attendance, payroll, reports
- [ ] Admin can manage users and departments
- [ ] Forgot password returns reset link in DEBUG mode
- [ ] Payroll generation works for an employee with attendance records
