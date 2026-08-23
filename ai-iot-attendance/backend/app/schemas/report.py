"""
Report schemas — structured responses for various report types.
"""

from pydantic import BaseModel


class StudentAttendanceSummary(BaseModel):
    """Per-student attendance summary for reports."""
    student_id: str
    name: str
    total_classes: int = 0
    present: int = 0
    absent: int = 0
    late: int = 0
    percentage: float = 0.0


class DailyReportResponse(BaseModel):
    """Daily attendance report for a course."""
    date: str
    course_id: str
    course_name: str = ""
    total_students: int = 0
    present: int = 0
    absent: int = 0
    late: int = 0
    percentage: float = 0.0
    records: list[StudentAttendanceSummary] = []


class DashboardStats(BaseModel):
    """Aggregated statistics for the teacher dashboard."""
    total_students: int = 0
    total_courses: int = 0
    active_sessions: int = 0
    today_present: int = 0
    today_absent: int = 0
    today_late: int = 0
    today_percentage: float = 0.0
    recent_records: list[dict] = []
