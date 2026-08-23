"""
Course management routes — CRUD, enrollment, and student listing.
"""

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_admin, require_teacher_or_admin
from app.schemas.auth import UserInToken
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseListResponse,
    EnrollmentCreate,
    EnrollmentResponse,
)
from app.services import course_service

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/", response_model=CourseListResponse)
async def list_courses(
    teacher_id: str | None = Query(None),
    department: str | None = Query(None),
    _: UserInToken = Depends(require_teacher_or_admin),
):
    """List all courses with optional filters."""
    return await course_service.list_courses(
        teacher_id=teacher_id, department=department
    )


@router.post(
    "/",
    response_model=CourseResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def create_course(data: CourseCreate):
    """Create a new course. Requires admin role."""
    return await course_service.create_course(data)


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    _: UserInToken = Depends(require_teacher_or_admin),
):
    """Get course details."""
    return await course_service.get_course(course_id)


@router.put(
    "/{course_id}",
    response_model=CourseResponse,
    dependencies=[Depends(require_admin)],
)
async def update_course(course_id: str, data: CourseUpdate):
    """Update a course. Requires admin role."""
    return await course_service.update_course(course_id, data)


@router.delete(
    "/{course_id}",
    dependencies=[Depends(require_admin)],
)
async def delete_course(course_id: str):
    """Delete a course and its enrollments. Requires admin role."""
    return await course_service.delete_course(course_id)


@router.get("/{course_id}/students")
async def get_course_students(
    course_id: str,
    _: UserInToken = Depends(require_teacher_or_admin),
):
    """List all students enrolled in a course."""
    return await course_service.get_course_students(course_id)


@router.post(
    "/{course_id}/enroll",
    response_model=EnrollmentResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def enroll_student(course_id: str, data: EnrollmentCreate):
    """Enroll a student in a course. Requires admin role."""
    # Override course_id from path
    data.course_id = course_id
    return await course_service.enroll_student(data)


@router.delete(
    "/{course_id}/enroll/{student_id}",
    dependencies=[Depends(require_admin)],
)
async def unenroll_student(course_id: str, student_id: str):
    """Remove a student from a course. Requires admin role."""
    return await course_service.unenroll_student(student_id, course_id)
