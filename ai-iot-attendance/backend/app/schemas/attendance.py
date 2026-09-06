"""
Attendance schemas — session management and attendance recording.
"""

from pydantic import BaseModel, field_validator
from typing import Optional

from app.schemas.common import normalize_timestamp


class SessionCreate(BaseModel):
    """Request body for starting an attendance session."""
    course_id: str
    late_threshold_minutes: int = 15
    device_id: str | None = None


class SessionUpdate(BaseModel):
    """Request body for ending/cancelling a session."""
    status: str  # "completed" or "cancelled"


class SessionResponse(BaseModel):
    """Attendance session data."""
    session_id: str
    course_id: str
    teacher_id: str
    session_date: str
    start_time: str
    end_time: str | None = None
    late_threshold_minutes: int
    status: str  # "active", "completed", "cancelled"
    device_id: str | None = None
    present_count: int = 0
    late_count: int = 0
    absent_count: int = 0

    @field_validator("session_date", "start_time", "end_time", mode="before")
    @classmethod
    def serialize_session_times(cls, value):
        return normalize_timestamp(value)


class AttendanceRecordCreate(BaseModel):
    """Request body for recording a student's attendance (from RPi)."""
    student_id: str
    confidence: float = 0.0
    method: str = "face"  # "face", "rfid", "manual"


class AttendanceRecordResponse(BaseModel):
    """Single attendance record."""
    record_id: str
    session_id: str
    student_id: str
    student_name: str = ""
    status: str  # "present", "absent", "late", "unknown", "rejected"
    confidence: float = 0.0
    detected_at: str
    method: str = "face"

    @field_validator("detected_at", mode="before")
    @classmethod
    def serialize_detected_at(cls, value):
        return normalize_timestamp(value)


class AttendanceSyncRequest(BaseModel):
    """Bulk sync request from RPi offline queue."""
    records: list[AttendanceRecordCreate]


class SessionDetailResponse(BaseModel):
    """Session details including attendance records."""
    session: SessionResponse
    records: list[AttendanceRecordResponse]
