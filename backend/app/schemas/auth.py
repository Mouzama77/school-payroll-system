from pydantic import BaseModel, EmailStr

class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    role: str = "employee"


class LoginSchema(BaseModel):
    email: EmailStr
    password: str