"""
Dashboard routes — aggregated statistics for the teacher dashboard.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas.auth import UserInToken
from app.schemas.report import DashboardStats
from app.services import report_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: UserInToken = Depends(get_current_user),
):
    """
    Get aggregated dashboard statistics.

    Returns: total students, courses, active sessions, today's counts.
    """
    return await report_service.get_dashboard_stats(current_user.user_id)
