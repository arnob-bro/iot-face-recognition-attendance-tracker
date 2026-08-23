"""
Course schemas — CRUD request/response models.
"""

from pydantic import BaseModel
from typing import Optional


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
