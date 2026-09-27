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
    password: str | None = None
    course_ids: list[str] = []


class StudentPasswordChange(BaseModel):
    """Self-service password change request."""
    current_password: str
    new_password: str


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
    must_change_password: bool = False
    created_at: str | None = None
    temporary_password: str | None = None

    @field_validator("created_at", mode="before")
    @classmethod
    def serialize_created_at(cls, value):
        """Normalize Firestore timestamps and ISO strings for API responses."""
        return normalize_timestamp(value)


class StudentListResponse(BaseModel):
    """Paginated list of students."""
    students: list[StudentResponse]
    total: int


class StudentAttendanceHistory(BaseModel):
    """Attendance result for one non-cancelled course session."""
    session_id: str
    session_date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    status: str
    detected_at: str | None = None
    method: str | None = None
    confidence: float | None = None

    @field_validator("session_date", "start_time", "end_time", "detected_at", mode="before")
    @classmethod
    def serialize_timestamps(cls, value):
        return normalize_timestamp(value)


class StudentCourseAttendance(BaseModel):
    """An enrolled course with the student's attendance summary and history."""
    course_id: str
    course_code: str
    course_name: str
    department: str
    section: str
    teacher_id: str
    enrolled_at: str | None = None
    total_classes: int = 0
    present: int = 0
    late: int = 0
    absent: int = 0
    percentage: float = 0.0
    attendance_history: list[StudentAttendanceHistory] = []

    @field_validator("enrolled_at", mode="before")
    @classmethod
    def serialize_enrolled_at(cls, value):
        return normalize_timestamp(value)
