"""Routine schemas for class scheduling and auto session generation."""

from pydantic import BaseModel, field_validator

from app.schemas.common import normalize_timestamp


class RoutineCreate(BaseModel):
    """Create a class routine for a course and time slot."""
    course_id: str
    teacher_id: str
    device_id: str | None = None
    room: str | None = None
    day_of_week: int = 0
    start_time: str
    end_time: str
    late_threshold_minutes: int = 15
    is_active: bool = True


class RoutineUpdate(BaseModel):
    """Update an existing routine; all fields optional."""
    course_id: str | None = None
    teacher_id: str | None = None
    device_id: str | None = None
    room: str | None = None
    day_of_week: int | None = None
    start_time: str | None = None
    end_time: str | None = None
    late_threshold_minutes: int | None = None
    is_active: bool | None = None


class RoutineResponse(BaseModel):
    """Routine returned by API endpoints."""
    routine_id: str
    course_id: str
    teacher_id: str
    device_id: str | None = None
    room: str | None = None
    day_of_week: int
    start_time: str
    end_time: str
    late_threshold_minutes: int
    is_active: bool = True
    created_at: str | None = None
    updated_at: str | None = None

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def serialize_timestamps(cls, value):
        return normalize_timestamp(value)


class RoutineListResponse(BaseModel):
    """List of class routines."""
    routines: list[RoutineResponse]
    total: int
