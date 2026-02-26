from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class UserRole(str, Enum):
    STUDENT = "student"
    TA = "ta"
    PROFESSOR = "professor"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)
    role: UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole
    token: str
