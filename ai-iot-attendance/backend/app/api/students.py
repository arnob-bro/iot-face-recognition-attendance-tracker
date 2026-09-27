"""
Student management routes — CRUD operations and attendance history.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_user, require_admin, require_student_or_self, require_teacher_or_admin
from app.schemas.auth import UserInToken
from app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentListResponse,
    StudentPasswordChange,
)
from app.schemas.attendance import AttendanceRecordResponse
from app.services import student_service, attendance_service

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("/login", response_model=dict)
async def login_student(student_id: str, password: str):
    """Authenticate a student using their student ID and password."""
    return await student_service.login_student(student_id, password)


@router.get("/me", response_model=StudentResponse)
async def get_me(current_user: UserInToken = Depends(get_current_user)):
    """Get the logged-in student's own profile."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="This endpoint is for student accounts only.")
    return await student_service.get_student(current_user.student_id or current_user.user_id)


@router.post("/me/change-password")
async def change_password(
    data: StudentPasswordChange,
    current_user: UserInToken = Depends(get_current_user),
):
    """Allow a student to change their own password."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only a student may change a student password.")
    return await student_service.change_password(current_user.student_id or current_user.user_id, data)


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
    current_user: UserInToken = Depends(get_current_user),
):
    """Get a student's details by their ID."""
    if current_user.role != "admin" and current_user.role != "teacher" and (current_user.role != "student" or current_user.student_id != student_id):
        raise HTTPException(status_code=403, detail="You can only access your own student record.")
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
    current_user: UserInToken = Depends(get_current_user),
):
    """Get a student's attendance history, optionally filtered by course."""
    if current_user.role not in ("admin", "teacher") and (current_user.role != "student" or current_user.student_id != student_id):
        raise HTTPException(status_code=403, detail="You can only access your own attendance record.")
    return await attendance_service.get_student_attendance(
        student_id, course_id=course_id
    )
