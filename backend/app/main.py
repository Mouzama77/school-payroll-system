from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.attendance import router as attendance_router
from app.api.audit_logs import router as audit_logs_router
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.departments import router as departments_router
from app.api.employees import router as employee_router
from app.api.payroll import router as payroll_router
from app.api.users import router as users_router
from app.core.config import settings
from app.db.session import SessionLocal
from app.api.leave import router as leave_router

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(users_router)
app.include_router(departments_router)
app.include_router(employee_router, prefix="/employees", tags=["Employees"])
app.include_router(attendance_router, prefix="/attendance", tags=["Attendance"])
app.include_router(payroll_router, prefix="/payroll", tags=["Payroll"])
app.include_router(dashboard_router)
app.include_router(leave_router)
app.include_router(audit_logs_router)

@app.get("/")
def root():
    return {"message": "School Payroll API is running"}


@app.get("/health")
def health_check():
    db_status = "ok"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        db_status = "error"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "environment": settings.APP_ENV,
    }
