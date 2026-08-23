"""
Authentication routes — login and teacher/admin registration.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, require_admin
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    TeacherCreate,
    TeacherResponse,
    UserInToken,
)
from app.services import auth_service

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
