from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.departments import router as departments_router
from app.api.employees import router as employee_router

app = FastAPI(title="School Payroll Management System")
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(departments_router)
app.include_router(employee_router, prefix="/employees", tags=["Employees"])


@app.get("/")
def root():
    return {"message": "School Payroll API is running"}