from fastapi import FastAPI

from app.api.auth import router as auth_router

app = FastAPI(title="School Payroll Management System")
app.include_router(auth_router, prefix="/auth", tags=["Auth"])


@app.get("/")
def root():
    return {"message": "School Payroll API is running"}
