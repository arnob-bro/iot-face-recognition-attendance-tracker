"""
Student schemas — CRUD request/response models.
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

from app.schemas.common import normalize_timestamp


class StudentCreate(BaseModel):
    """Request body for creating a new student."""
    student_id: str
    name: str
    department: str
    batch: str
    email: EmailStr
    course_ids: list[str] = []


class StudentUpdate(BaseModel):
    """Request body for updating an existing student. All fields optional."""
    name: Optional[str] = None
    department: Optional[str] = None
    batch: Optional[str] = None
    email: Optional[EmailStr] = None


class StudentResponse(BaseModel):
    """Student public data returned by the API."""
    student_id: str
    name: str
    department: str
    batch: str
    email: str
    is_active: bool = True
    face_enrolled: bool = False
    created_at: str | None = None

    @field_validator("created_at", mode="before")
    @classmethod
    def serialize_created_at(cls, value):
        """Normalize Firestore timestamps and ISO strings for API responses."""
        return normalize_timestamp(value)


class StudentListResponse(BaseModel):
    """Paginated list of students."""
    students: list[StudentResponse]
    total: int
