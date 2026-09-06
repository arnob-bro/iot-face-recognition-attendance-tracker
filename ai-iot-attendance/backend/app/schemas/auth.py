"""
Authentication schemas — login request/response and token models.
"""

from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.common import normalize_timestamp


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


class DeviceLoginRequest(BaseModel):
    """Credentials used by a Raspberry Pi device."""
    device_id: str
    device_secret: str


class DeviceCreate(BaseModel):
    """Request body for registering a Raspberry Pi device."""
    device_id: str
    name: str
    location: str = ""


class DeviceResponse(BaseModel):
    """Registered Raspberry Pi device."""
    device_id: str
    name: str
    location: str = ""
    enabled: bool = True
    last_seen_at: str | None = None

    @field_validator("last_seen_at", mode="before")
    @classmethod
    def serialize_last_seen_at(cls, value):
        return normalize_timestamp(value)


class DeviceCreateResponse(DeviceResponse):
    """Device response containing the one-time generated secret."""
    device_secret: str


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

    @field_validator("created_at", mode="before")
    @classmethod
    def serialize_created_at(cls, value):
        return normalize_timestamp(value)


class UserInToken(BaseModel):
    """The user identity extracted from a validated JWT."""
    user_id: str
    email: str
    role: str
    device_id: str | None = None
