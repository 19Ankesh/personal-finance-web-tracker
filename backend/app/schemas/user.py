"""
Pydantic schemas for the User domain.

Schemas:
  UserCreate    – registration input
  UserUpdate    – profile update input
  UserResponse  – public user data returned by API
  UserLogin     – login input (JSON body)
  TokenResponse – JWT token + user returned after auth
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserCreate(BaseModel):
    """Input schema for user registration."""

    name: str
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty.")
        if len(v) > 255:
            raise ValueError("Name must be 255 characters or fewer.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters.")
        return v


class UserUpdate(BaseModel):
    """Input schema for updating a user profile."""

    name: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Name cannot be empty.")
        return v


class UserResponse(BaseModel):
    """Public user data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    created_at: datetime


class UserLogin(BaseModel):
    """Input schema for JSON-body login (used by Postman / Insomnia)."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Returned after successful registration or login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ForgotPasswordRequest(BaseModel):
    """Input schema for requesting a password reset email."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Input schema for resetting a password using a JWT token."""

    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters.")
        return v
