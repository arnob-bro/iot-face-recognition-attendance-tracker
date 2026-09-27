"""Routine API routes for class schedules and auto session management."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user, require_admin, require_teacher_or_admin
from app.schemas.auth import UserInToken
from app.schemas.routine import RoutineCreate, RoutineListResponse, RoutineResponse, RoutineUpdate
from app.services import routine_service

router = APIRouter(prefix="/routines", tags=["Class Routines"])


@router.get("/", response_model=RoutineListResponse)
async def list_routines(
    current_user: UserInToken = Depends(get_current_user),
):
    """List routines. Admin sees all; teacher sees their own routines."""
    if current_user.role == "admin":
        routines = await routine_service.list_routines()
    else:
        routines = await routine_service.list_routines(teacher_id=current_user.user_id)
    return {"routines": routines, "total": len(routines)}


@router.post("/", response_model=RoutineResponse, status_code=201)
async def create_routine(
    data: RoutineCreate,
    _: UserInToken = Depends(require_admin),
):
    """Create a new routine. Admin-only."""
    saved = await routine_service.create_routine(data.model_dump())
    return RoutineResponse(**saved)


@router.get("/{routine_id}", response_model=RoutineResponse)
async def get_routine(
    routine_id: str,
    current_user: UserInToken = Depends(get_current_user),
):
    """Get one routine; teacher may only fetch their own routine."""
    routine = await routine_service.get_routine(routine_id)
    if current_user.role == "teacher" and routine.get("teacher_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only view your own routines.")
    return RoutineResponse(**routine)


@router.put("/{routine_id}", response_model=RoutineResponse)
async def update_routine(
    routine_id: str,
    data: RoutineUpdate,
    _: UserInToken = Depends(require_admin),
):
    """Update a routine. Admin-only."""
    saved = await routine_service.update_routine(routine_id, data.model_dump(exclude_none=True))
    return RoutineResponse(**saved)


@router.delete("/{routine_id}")
async def delete_routine(
    routine_id: str,
    _: UserInToken = Depends(require_admin),
):
    """Delete a routine. Admin-only."""
    return await routine_service.delete_routine(routine_id)
