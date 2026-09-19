"""
Authentication routes — login and teacher/admin registration.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user, require_admin
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    TeacherCreate,
    TeacherResponse,
    UserInToken,
)
from app.services import auth_service
from app.services.auth_service import get_all_teachers, get_teacher_by_id

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate with email and password. Returns a JWT token."""
    return await auth_service.login(request)


@router.post(
    "/register",
    response_model=TeacherResponse,
    dependencies=[Depends(require_admin)],
)
async def register_teacher(data: TeacherCreate):
    """Create a new teacher or admin account. Requires admin role."""
    return await auth_service.register_teacher(data)


@router.get("/me", response_model=TeacherResponse)
async def get_me(current_user: UserInToken = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return await auth_service.get_current_user(current_user.user_id)


@router.get("/teachers", response_model=list[TeacherResponse])
async def list_teachers(current_user: UserInToken = Depends(get_current_user)):
    """List teachers.

    Admins can see all teachers/admins. Teachers can only see their own profile.
    """
    if current_user.role == "admin":
        return await get_all_teachers()

    if current_user.role == "teacher":
        return [await auth_service.get_current_user(current_user.user_id)]

    raise HTTPException(status_code=403, detail="This action requires teacher or admin privileges.")


@router.get("/teachers/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(
    teacher_id: str,
    current_user: UserInToken = Depends(get_current_user),
):
    """Get a teacher profile.

    Admin can view any teacher. Teacher can only view their own profile.
    """
    teacher = await get_teacher_by_id(teacher_id)

    if current_user.role == "admin":
        return teacher

    if current_user.role == "teacher" and current_user.user_id == teacher_id:
        return teacher

    raise HTTPException(status_code=403, detail="You are not allowed to view this teacher profile.")
