"""
Attendance service — session management and attendance recording.

Implements session-based attendance with:
- Duplicate prevention (one record per student per session)
- Late detection (configurable threshold per session)
- Absent marking (when session ends, unmarked students are absent)
- Bulk sync (for offline RPi queue)
"""

import logging
from datetime import datetime, timezone, timedelta

from app.core.firebase import get_db
from app.core.exceptions import (
    NotFoundError,
    DuplicateError,
    ValidationError,
)
from app.schemas.attendance import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    AttendanceRecordCreate,
    AttendanceRecordResponse,
    SessionDetailResponse,
)

logger = logging.getLogger(__name__)

SESSIONS_COLLECTION = "attendance_sessions"
RECORDS_COLLECTION = "attendance_records"
COURSES_COLLECTION = "courses"
ENROLLMENTS_COLLECTION = "enrollments"


async def start_session(
    data: SessionCreate, teacher_id: str
) -> SessionResponse:
    """
    Start a new attendance session for a course.

    Only one active session per course is allowed at a time.
    """
    db = get_db()

    # Verify course exists
    course_doc = db.collection(COURSES_COLLECTION).document(data.course_id).get()
    if not course_doc.exists:
        raise NotFoundError("Course", data.course_id)

    # Check for existing active session on same course
    existing = (
        db.collection(SESSIONS_COLLECTION)
        .where("course_id", "==", data.course_id)
        .where("status", "==", "active")
        .limit(1)
        .get()
    )
    if existing:
        raise DuplicateError(
            "Active session",
            f"course {data.course_id}",
        )

    now = datetime.now(timezone.utc)
    doc_data = {
        "course_id": data.course_id,
        "teacher_id": teacher_id,
        "session_date": now.strftime("%Y-%m-%d"),
        "start_time": now.isoformat(),
        "end_time": None,
        "late_threshold_minutes": data.late_threshold_minutes,
        "status": "active",
    }

    doc_ref = db.collection(SESSIONS_COLLECTION).add(doc_data)
    session_id = doc_ref[1].id

    # Increment total_classes counter on the course
    course_doc.reference.update({
        "total_classes": (course_doc.to_dict().get("total_classes", 0) + 1)
    })

    logger.info(
        f"Started session {session_id} for course {data.course_id} "
        f"(late threshold: {data.late_threshold_minutes}min)"
    )

    return SessionResponse(
        session_id=session_id,
        **doc_data,
    )


async def end_session(
    session_id: str, data: SessionUpdate, teacher_id: str
) -> SessionResponse:
    """
    End or cancel an attendance session.

    When ending (status='completed'), marks all unmarked enrolled students
    as absent.
    """
    db = get_db()
    doc_ref = db.collection(SESSIONS_COLLECTION).document(session_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise NotFoundError("Session", session_id)

    session_data = doc.to_dict()

    if session_data["status"] != "active":
        raise ValidationError(
            f"Session is already '{session_data['status']}'. "
            "Only active sessions can be updated."
        )

    now = datetime.now(timezone.utc).isoformat()
    doc_ref.update({
        "status": data.status,
        "end_time": now,
    })

    # If completing (not cancelling), mark absent students
    if data.status == "completed":
        await _mark_absent_students(db, session_id, session_data["course_id"])

    logger.info(f"Session {session_id} → {data.status}")

    session_data.update({"status": data.status, "end_time": now})
    counts = await _get_session_counts(db, session_id)

    return SessionResponse(
        session_id=session_id,
        **session_data,
        **counts,
    )


async def record_attendance(
    session_id: str, data: AttendanceRecordCreate
) -> AttendanceRecordResponse:
    """
    Record a single attendance entry for a student in a session.

    Implements:
    - Duplicate prevention: skips if student already recorded in this session
    - Late detection: checks timestamp against session start + threshold
    """
    db = get_db()

    # Verify session exists and is active
    session_doc = db.collection(SESSIONS_COLLECTION).document(session_id).get()
    if not session_doc.exists:
        raise NotFoundError("Session", session_id)

    session_data = session_doc.to_dict()
    if session_data["status"] != "active":
        raise ValidationError("Cannot record attendance for an inactive session.")

    # Duplicate check: one record per student per session
    existing = (
        db.collection(RECORDS_COLLECTION)
        .where("session_id", "==", session_id)
        .where("student_id", "==", data.student_id)
        .limit(1)
        .get()
    )
    if existing:
        # Return the existing record instead of creating a duplicate
        existing_data = existing[0].to_dict()
        return AttendanceRecordResponse(
            record_id=existing[0].id,
            **existing_data,
        )

    # Determine status: present or late
    now = datetime.now(timezone.utc)
    start_time = datetime.fromisoformat(session_data["start_time"])
    late_threshold = start_time + timedelta(
        minutes=session_data["late_threshold_minutes"]
    )

    status = "present" if now <= late_threshold else "late"

    # Look up student name for the response
    student_name = ""
    student_doc = db.collection("students").document(data.student_id).get()
    if student_doc.exists:
        student_name = student_doc.to_dict().get("name", "")

    record_data = {
        "session_id": session_id,
        "student_id": data.student_id,
        "student_name": student_name,
        "status": status,
        "confidence": data.confidence,
        "detected_at": now.isoformat(),
        "method": data.method,
    }

    doc_ref = db.collection(RECORDS_COLLECTION).add(record_data)
    record_id = doc_ref[1].id

    logger.info(
        f"Attendance: {data.student_id} → {status} "
        f"(confidence={data.confidence:.2f}, method={data.method})"
    )

    return AttendanceRecordResponse(record_id=record_id, **record_data)


async def bulk_sync_records(
    session_id: str, records: list[AttendanceRecordCreate]
) -> list[AttendanceRecordResponse]:
    """
    Bulk sync attendance records from RPi offline queue.

    Each record is processed individually with the same duplicate
    prevention logic as single recording, making this idempotent.
    """
    results = []
    for record_data in records:
        result = await record_attendance(session_id, record_data)
        results.append(result)

    logger.info(f"Bulk synced {len(results)} records for session {session_id}")
    return results


async def get_session(session_id: str) -> SessionDetailResponse:
    """Get session details including all attendance records."""
    db = get_db()
    doc = db.collection(SESSIONS_COLLECTION).document(session_id).get()

    if not doc.exists:
        raise NotFoundError("Session", session_id)

    session_data = doc.to_dict()
    counts = await _get_session_counts(db, session_id)

    # Get all records for this session
    record_docs = (
        db.collection(RECORDS_COLLECTION)
        .where("session_id", "==", session_id)
        .get()
    )
    records = [
        AttendanceRecordResponse(record_id=rdoc.id, **rdoc.to_dict())
        for rdoc in record_docs
    ]

    session = SessionResponse(
        session_id=session_id,
        **session_data,
        **counts,
    )

    return SessionDetailResponse(session=session, records=records)


async def get_active_session(
    course_id: str | None = None,
) -> SessionResponse | None:
    """Get the currently active session, optionally for a specific course."""
    db = get_db()
    query = db.collection(SESSIONS_COLLECTION).where("status", "==", "active")

    if course_id:
        query = query.where("course_id", "==", course_id)

    docs = query.limit(1).get()

    if not docs:
        return None

    doc = docs[0]
    session_data = doc.to_dict()
    counts = await _get_session_counts(db, doc.id)

    return SessionResponse(
        session_id=doc.id,
        **session_data,
        **counts,
    )


async def get_student_attendance(
    student_id: str,
    course_id: str | None = None,
) -> list[AttendanceRecordResponse]:
    """Get all attendance records for a student, optionally filtered by course."""
    db = get_db()

    query = db.collection(RECORDS_COLLECTION).where(
        "student_id", "==", student_id
    )

    record_docs = query.get()
    records = []

    for rdoc in record_docs:
        rdata = rdoc.to_dict()

        # If filtering by course, check the session's course_id
        if course_id:
            session_doc = (
                db.collection(SESSIONS_COLLECTION)
                .document(rdata["session_id"])
                .get()
            )
            if session_doc.exists:
                sdata = session_doc.to_dict()
                if sdata.get("course_id") != course_id:
                    continue

        records.append(
            AttendanceRecordResponse(record_id=rdoc.id, **rdata)
        )

    return records


async def _mark_absent_students(
    db, session_id: str, course_id: str
) -> None:
    """
    Mark enrolled students who have no attendance record in this session
    as 'absent'. Called when a session is completed.
    """
    # Get all enrolled student IDs for this course
    enrollment_docs = (
        db.collection(ENROLLMENTS_COLLECTION)
        .where("course_id", "==", course_id)
        .get()
    )
    enrolled_ids = {doc.to_dict()["student_id"] for doc in enrollment_docs}

    # Get student IDs already recorded in this session
    record_docs = (
        db.collection(RECORDS_COLLECTION)
        .where("session_id", "==", session_id)
        .get()
    )
    recorded_ids = {doc.to_dict()["student_id"] for doc in record_docs}

    # Absent = enrolled but not recorded
    absent_ids = enrolled_ids - recorded_ids

    now = datetime.now(timezone.utc).isoformat()
    for student_id in absent_ids:
        student_name = ""
        student_doc = db.collection("students").document(student_id).get()
        if student_doc.exists:
            student_name = student_doc.to_dict().get("name", "")

        db.collection(RECORDS_COLLECTION).add({
            "session_id": session_id,
            "student_id": student_id,
            "student_name": student_name,
            "status": "absent",
            "confidence": 0.0,
            "detected_at": now,
            "method": "auto",
        })

    if absent_ids:
        logger.info(
            f"Marked {len(absent_ids)} students as absent "
            f"for session {session_id}"
        )


async def _get_session_counts(db, session_id: str) -> dict:
    """Get attendance counts for a session."""
    record_docs = (
        db.collection(RECORDS_COLLECTION)
        .where("session_id", "==", session_id)
        .get()
    )

    counts = {"present_count": 0, "late_count": 0, "absent_count": 0}
    for rdoc in record_docs:
        status = rdoc.to_dict().get("status", "")
        if status == "present":
            counts["present_count"] += 1
        elif status == "late":
            counts["late_count"] += 1
        elif status == "absent":
            counts["absent_count"] += 1

    return counts
