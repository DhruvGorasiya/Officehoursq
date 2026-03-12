from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr = Field(description="User's email address")
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password, minimum 8 characters",
    )
    name: str = Field(
        min_length=1,
        max_length=100,
        description="User's display name",
    )
    role: UserRole = Field(
        description="User role: student, ta, or professor",
    )


class LoginRequest(BaseModel):
    email: EmailStr = Field(description="Registered email address")
    password: str = Field(description="Account password")


class UserResponse(BaseModel):
    id: UUID = Field(description="Unique user identifier")
    email: str = Field(description="User's email")
    name: str = Field(description="User's display name")
    role: UserRole = Field(description="User's role")
    created_at: datetime = Field(description="Account creation timestamp")


class AuthResponse(BaseModel):
    id: UUID = Field(description="Unique user identifier")
    email: str = Field(description="User's email")
    name: str = Field(description="User's display name")
    role: UserRole = Field(description="User's role")
    token: str = Field(description="JWT access token for authenticated requests")
