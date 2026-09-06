"""
Course schemas — CRUD request/response models.
"""

from pydantic import BaseModel, field_validator
from typing import Optional

from app.schemas.common import normalize_timestamp


class CourseCreate(BaseModel):
    """Request body for creating a new course."""
    course_code: str
    course_name: str
    department: str
    section: str
    teacher_id: str


class CourseUpdate(BaseModel):
    """Request body for updating a course. All fields optional."""
    course_name: Optional[str] = None
    department: Optional[str] = None
    section: Optional[str] = None
    teacher_id: Optional[str] = None


class CourseResponse(BaseModel):
    """Course data returned by the API."""
    course_id: str
    course_code: str
    course_name: str
    department: str
    section: str
    teacher_id: str
    total_classes: int = 0
    created_at: str | None = None

    @field_validator("created_at", mode="before")
    @classmethod
    def serialize_created_at(cls, value):
        """Normalize Firestore timestamps for API responses."""
        return normalize_timestamp(value)


class CourseListResponse(BaseModel):
    """List of courses."""
    courses: list[CourseResponse]
    total: int


class EnrollmentCreate(BaseModel):
    """Enroll a student in a course."""
    student_id: str
    course_id: str


class EnrollmentResponse(BaseModel):
    """Enrollment record."""
    enrollment_id: str
    student_id: str
    course_id: str
    enrolled_at: str | None = None

    @field_validator("enrolled_at", mode="before")
    @classmethod
    def serialize_enrolled_at(cls, value):
        """Normalize Firestore timestamps for API responses."""
        return normalize_timestamp(value)
