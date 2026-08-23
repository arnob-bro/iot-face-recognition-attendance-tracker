"""
Student schemas — CRUD request/response models.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional


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


class StudentListResponse(BaseModel):
    """Paginated list of students."""
    students: list[StudentResponse]
    total: int
