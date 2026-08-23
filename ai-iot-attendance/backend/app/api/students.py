"""
Student management routes — CRUD operations and attendance history.
"""

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, require_admin, require_teacher_or_admin
from app.schemas.auth import UserInToken
from app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentListResponse,
)
from app.schemas.attendance import AttendanceRecordResponse
from app.services import student_service, attendance_service

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/", response_model=StudentListResponse)
async def list_students(
    department: str | None = Query(None),
    batch: str | None = Query(None),
    course_id: str | None = Query(None),
    _: UserInToken = Depends(require_teacher_or_admin),
):
    """List all students with optional filters."""
    return await student_service.list_students(
        department=department, batch=batch, course_id=course_id
    )


@router.post(
    "/",
    response_model=StudentResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def create_student(data: StudentCreate):
    """Create a new student. Requires admin role."""
    return await student_service.create_student(data)


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: str,
    _: UserInToken = Depends(require_teacher_or_admin),
):
    """Get a student's details by their ID."""
    return await student_service.get_student(student_id)


@router.put(
    "/{student_id}",
    response_model=StudentResponse,
    dependencies=[Depends(require_admin)],
)
async def update_student(student_id: str, data: StudentUpdate):
    """Update a student's information. Requires admin role."""
    return await student_service.update_student(student_id, data)


@router.delete(
    "/{student_id}",
    dependencies=[Depends(require_admin)],
)
async def delete_student(student_id: str):
    """Deactivate a student. Requires admin role."""
    return await student_service.delete_student(student_id)


@router.get(
    "/{student_id}/attendance",
    response_model=list[AttendanceRecordResponse],
)
async def get_student_attendance(
    student_id: str,
    course_id: str | None = Query(None),
    _: UserInToken = Depends(require_teacher_or_admin),
):
    """Get a student's attendance history, optionally filtered by course."""
    return await attendance_service.get_student_attendance(
        student_id, course_id=course_id
    )
