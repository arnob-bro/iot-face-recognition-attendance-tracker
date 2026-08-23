"""
Authentication schemas — login request/response and token models.
"""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login credentials."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response returned after successful login."""
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str


class TeacherCreate(BaseModel):
    """Request body for creating a new teacher/admin account."""
    name: str
    email: EmailStr
    password: str
    role: str = "teacher"  # "admin" or "teacher"


class TeacherResponse(BaseModel):
    """Teacher/admin public profile."""
    teacher_id: str
    name: str
    email: str
    role: str
    created_at: str | None = None


class UserInToken(BaseModel):
    """The user identity extracted from a validated JWT."""
    user_id: str
    email: str
    role: str
