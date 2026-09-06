"""
Attendance routes — session management and attendance recording.

Sessions are started/ended by teachers. Individual attendance records
are submitted by the Raspberry Pi client or manually.
"""

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, require_teacher_or_admin
from app.schemas.auth import UserInToken
from app.schemas.attendance import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    AttendanceRecordCreate,
    AttendanceRecordResponse,
    AttendanceSyncRequest,
    SessionDetailResponse,
)
from app.services import attendance_service

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=201,
)
async def start_session(
    data: SessionCreate,
    current_user: UserInToken = Depends(require_teacher_or_admin),
):
    """Start a new attendance session for a course."""
    return await attendance_service.start_session(data, current_user.user_id)


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    data: SessionUpdate,
    current_user: UserInToken = Depends(require_teacher_or_admin),
):
    """End or cancel an attendance session."""
    return await attendance_service.end_session(
        session_id, data, current_user.user_id
    )


@router.get("/sessions/active", response_model=SessionResponse | None)
async def get_active_session(
    course_id: str | None = Query(None),
    current_user: UserInToken = Depends(get_current_user),
):
    """Get the currently active attendance session."""
    return await attendance_service.get_active_session(
        course_id, current_user.device_id
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    _: UserInToken = Depends(require_teacher_or_admin),
):
    """Get session details including all attendance records."""
    return await attendance_service.get_session(session_id)


@router.post(
    "/sessions/{session_id}/record",
    response_model=AttendanceRecordResponse,
    status_code=201,
)
async def record_attendance(
    session_id: str,
    data: AttendanceRecordCreate,
    current_user: UserInToken = Depends(get_current_user),
):
    """
    Record a single attendance entry.

    Typically called by the Raspberry Pi client after face recognition.
    Handles duplicate prevention automatically.
    """
    return await attendance_service.record_attendance(
        session_id, data, current_user.device_id
    )


@router.post(
    "/sessions/{session_id}/sync",
    response_model=list[AttendanceRecordResponse],
)
async def sync_records(
    session_id: str,
    data: AttendanceSyncRequest,
    current_user: UserInToken = Depends(get_current_user),
):
    """
    Bulk sync attendance records from the RPi offline queue.

    Idempotent — duplicate records are skipped automatically.
    """
    return await attendance_service.bulk_sync_records(
        session_id, data.records, current_user.device_id
    )
