"""
Report service — generates attendance reports and dashboard statistics.

Provides daily, weekly, monthly, course-wise, and student-wise reports
with aggregated counts and percentages. Also provides CSV-exportable data.
"""

import logging
from datetime import datetime, timezone, timedelta

from app.core.firebase import get_db
from app.schemas.report import (
    StudentAttendanceSummary,
    DailyReportResponse,
    DashboardStats,
)

logger = logging.getLogger(__name__)

SESSIONS_COLLECTION = "attendance_sessions"
RECORDS_COLLECTION = "attendance_records"
STUDENTS_COLLECTION = "students"
COURSES_COLLECTION = "courses"
ENROLLMENTS_COLLECTION = "enrollments"


async def get_dashboard_stats(teacher_id: str) -> DashboardStats:
    """
    Get aggregated dashboard statistics for the teacher.

    Includes: total students, courses, active sessions, today's counts.
    """
    db = get_db()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Count students
    student_docs = db.collection(STUDENTS_COLLECTION).get()
    total_students = len(student_docs)

    # Count courses (teacher's own courses)
    course_docs = (
        db.collection(COURSES_COLLECTION)
        .where("teacher_id", "==", teacher_id)
        .get()
    )
    total_courses = len(course_docs)

    # Active sessions
    active_docs = (
        db.collection(SESSIONS_COLLECTION)
        .where("status", "==", "active")
        .get()
    )
    active_sessions = len(active_docs)

    # Today's attendance across all sessions
    today_sessions = (
        db.collection(SESSIONS_COLLECTION)
        .where("session_date", "==", today)
        .get()
    )

    today_present = 0
    today_absent = 0
    today_late = 0
    recent_records = []

    for sdoc in today_sessions:
        record_docs = (
            db.collection(RECORDS_COLLECTION)
            .where("session_id", "==", sdoc.id)
            .get()
        )
        for rdoc in record_docs:
            rdata = rdoc.to_dict()
            status = rdata.get("status", "")
            if status == "present":
                today_present += 1
            elif status == "absent":
                today_absent += 1
            elif status == "late":
                today_late += 1

            # Collect recent records for the activity feed
            recent_records.append({
                "student_id": rdata.get("student_id", ""),
                "student_name": rdata.get("student_name", ""),
                "status": status,
                "detected_at": rdata.get("detected_at", ""),
                "confidence": rdata.get("confidence", 0.0),
            })

    # Sort recent records by time and take last 10
    recent_records.sort(key=lambda r: r.get("detected_at", ""), reverse=True)
    recent_records = recent_records[:10]

    total_today = today_present + today_absent + today_late
    today_percentage = (
        round((today_present + today_late) / total_today * 100, 1)
        if total_today > 0
        else 0.0
    )

    return DashboardStats(
        total_students=total_students,
        total_courses=total_courses,
        active_sessions=active_sessions,
        today_present=today_present,
        today_absent=today_absent,
        today_late=today_late,
        today_percentage=today_percentage,
        recent_records=recent_records,
    )


async def get_daily_report(
    course_id: str, date: str
) -> DailyReportResponse:
    """
    Generate a daily attendance report for a specific course and date.

    Lists each enrolled student's status for that day.
    """
    db = get_db()

    # Get course info
    course_doc = db.collection(COURSES_COLLECTION).document(course_id).get()
    course_name = ""
    if course_doc.exists:
        course_name = course_doc.to_dict().get("course_name", "")

    # Find sessions for this course on this date
    sessions = (
        db.collection(SESSIONS_COLLECTION)
        .where("course_id", "==", course_id)
        .where("session_date", "==", date)
        .get()
    )

    records_list = []
    total_present = 0
    total_absent = 0
    total_late = 0

    for sdoc in sessions:
        record_docs = (
            db.collection(RECORDS_COLLECTION)
            .where("session_id", "==", sdoc.id)
            .get()
        )
        for rdoc in record_docs:
            rdata = rdoc.to_dict()
            status = rdata.get("status", "unknown")
            if status == "present":
                total_present += 1
            elif status == "absent":
                total_absent += 1
            elif status == "late":
                total_late += 1

            records_list.append(
                StudentAttendanceSummary(
                    student_id=rdata.get("student_id", ""),
                    name=rdata.get("student_name", ""),
                    total_classes=1,
                    present=1 if status == "present" else 0,
                    absent=1 if status == "absent" else 0,
                    late=1 if status == "late" else 0,
                    percentage=100.0 if status in ("present", "late") else 0.0,
                )
            )

    total = total_present + total_absent + total_late
    percentage = (
        round((total_present + total_late) / total * 100, 1)
        if total > 0
        else 0.0
    )

    return DailyReportResponse(
        date=date,
        course_id=course_id,
        course_name=course_name,
        total_students=total,
        present=total_present,
        absent=total_absent,
        late=total_late,
        percentage=percentage,
        records=records_list,
    )


async def get_course_report(
    course_id: str,
) -> list[StudentAttendanceSummary]:
    """
    Generate a course-wide attendance summary for all students.

    Shows total classes, present, absent, late, percentage for each student.
    """
    db = get_db()

    # Get all enrolled students
    enrollment_docs = (
        db.collection(ENROLLMENTS_COLLECTION)
        .where("course_id", "==", course_id)
        .get()
    )

    # Get all sessions for this course
    session_docs = (
        db.collection(SESSIONS_COLLECTION)
        .where("course_id", "==", course_id)
        .get()
    )
    session_ids = [sdoc.id for sdoc in session_docs]
    total_classes = len(session_ids)

    summaries = []
    for edoc in enrollment_docs:
        edata = edoc.to_dict()
        student_id = edata["student_id"]

        # Get student name
        student_doc = db.collection(STUDENTS_COLLECTION).document(student_id).get()
        name = student_doc.to_dict().get("name", "") if student_doc.exists else ""

        # Count statuses across all sessions
        present = 0
        absent = 0
        late = 0

        for session_id in session_ids:
            record_docs = (
                db.collection(RECORDS_COLLECTION)
                .where("session_id", "==", session_id)
                .where("student_id", "==", student_id)
                .limit(1)
                .get()
            )
            if record_docs:
                status = record_docs[0].to_dict().get("status", "absent")
                if status == "present":
                    present += 1
                elif status == "late":
                    late += 1
                else:
                    absent += 1
            else:
                absent += 1

        percentage = (
            round((present + late) / total_classes * 100, 1)
            if total_classes > 0
            else 0.0
        )

        summaries.append(
            StudentAttendanceSummary(
                student_id=student_id,
                name=name,
                total_classes=total_classes,
                present=present,
                absent=absent,
                late=late,
                percentage=percentage,
            )
        )

    return summaries


async def get_student_report(
    student_id: str,
) -> list[dict]:
    """
    Generate an attendance summary for a student across all their courses.
    """
    db = get_db()

    # Get all courses the student is enrolled in
    enrollment_docs = (
        db.collection(ENROLLMENTS_COLLECTION)
        .where("student_id", "==", student_id)
        .get()
    )

    report = []
    for edoc in enrollment_docs:
        course_id = edoc.to_dict()["course_id"]
        course_doc = db.collection(COURSES_COLLECTION).document(course_id).get()

        if not course_doc.exists:
            continue

        cdata = course_doc.to_dict()

        # Get all sessions for this course
        session_docs = (
            db.collection(SESSIONS_COLLECTION)
            .where("course_id", "==", course_id)
            .get()
        )

        total = len(session_docs)
        present = 0
        late = 0
        absent = 0

        for sdoc in session_docs:
            rdocs = (
                db.collection(RECORDS_COLLECTION)
                .where("session_id", "==", sdoc.id)
                .where("student_id", "==", student_id)
                .limit(1)
                .get()
            )
            if rdocs:
                status = rdocs[0].to_dict().get("status", "absent")
                if status == "present":
                    present += 1
                elif status == "late":
                    late += 1
                else:
                    absent += 1
            else:
                absent += 1

        percentage = (
            round((present + late) / total * 100, 1) if total > 0 else 0.0
        )

        report.append({
            "course_id": course_id,
            "course_code": cdata.get("course_code", ""),
            "course_name": cdata.get("course_name", ""),
            "total_classes": total,
            "present": present,
            "late": late,
            "absent": absent,
            "percentage": percentage,
        })

    return report


async def get_report_csv_data(
    course_id: str | None = None,
    student_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """
    Generate raw attendance data suitable for CSV export.

    Returns flat records with all relevant fields.
    """
    db = get_db()
    query = db.collection(RECORDS_COLLECTION)

    record_docs = query.get()
    rows = []

    for rdoc in record_docs:
        rdata = rdoc.to_dict()
        session_id = rdata.get("session_id", "")

        # Get session data for course and date filtering
        session_doc = db.collection(SESSIONS_COLLECTION).document(session_id).get()
        if not session_doc.exists:
            continue

        sdata = session_doc.to_dict()

        # Apply filters
        if course_id and sdata.get("course_id") != course_id:
            continue
        if student_id and rdata.get("student_id") != student_id:
            continue
        if start_date and sdata.get("session_date", "") < start_date:
            continue
        if end_date and sdata.get("session_date", "") > end_date:
            continue

        # Get course name
        course_doc = (
            db.collection(COURSES_COLLECTION)
            .document(sdata.get("course_id", ""))
            .get()
        )
        course_name = (
            course_doc.to_dict().get("course_name", "")
            if course_doc.exists
            else ""
        )

        rows.append({
            "date": sdata.get("session_date", ""),
            "course_code": sdata.get("course_id", ""),
            "course_name": course_name,
            "student_id": rdata.get("student_id", ""),
            "student_name": rdata.get("student_name", ""),
            "status": rdata.get("status", ""),
            "time": rdata.get("detected_at", ""),
            "method": rdata.get("method", ""),
            "confidence": rdata.get("confidence", 0.0),
        })

    return rows
