"""
Student service — CRUD operations for students in Firebase.

Students are stored in the 'students' collection keyed by their
university-issued student_id (e.g., "20220104064").
"""

import logging
from datetime import datetime, timezone

from app.core.firebase import get_db
from app.core.exceptions import NotFoundError, DuplicateError, AuthenticationError
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentListResponse,
    StudentPasswordChange,
)

logger = logging.getLogger(__name__)

STUDENTS_COLLECTION = "students"
FACE_EMBEDDINGS_COLLECTION = "face_embeddings"


async def login_student(student_id: str, password: str) -> dict:
    """Authenticate a student and return a JWT payload."""
    db = get_db()
    doc = db.collection(STUDENTS_COLLECTION).document(student_id).get()
    if not doc.exists:
        raise AuthenticationError("Invalid student credentials.")

    student_data = doc.to_dict()
    if not student_data.get("password_hash"):
        raise AuthenticationError("This student account has no password set.")
    if not verify_password(password, student_data["password_hash"]):
        raise AuthenticationError("Invalid student credentials.")

    token = create_access_token({
        "sub": student_id,
        "email": student_data.get("email", ""),
        "role": "student",
        "student_id": student_id,
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": "student",
        "name": student_data.get("name", student_id),
    }


async def change_password(
    student_id: str,
    data: StudentPasswordChange
) -> dict:
    """Change password for an authenticated student."""

    db = get_db()

    doc_ref = db.collection(STUDENTS_COLLECTION).document(student_id)

    doc = doc_ref.get()

    if not doc.exists:
        raise NotFoundError("Student", student_id)


    student_data = doc.to_dict()


    if not student_data.get("password_hash"):
        raise AuthenticationError(
            "This student account has no password set."
        )


    if not verify_password(
        data.current_password,
        student_data["password_hash"]
    ):
        raise AuthenticationError(
            "Current password is incorrect."
        )


    new_password_hash = hash_password(
        data.new_password
    )


    doc_ref.update({
        "password_hash": new_password_hash,
        "must_change_password": False,
    })


    logger.info(
        f"Student {student_id} changed password."
    )


    return {
        "message": "Password changed successfully."
    }




async def create_student(data: StudentCreate) -> StudentResponse:
    """Create a new student. Uses student_id as the document ID."""
    db = get_db()

    # Check for duplicate student_id
    doc_ref = db.collection(STUDENTS_COLLECTION).document(data.student_id)
    if doc_ref.get().exists:
        raise DuplicateError("Student", data.student_id)

    now = datetime.now(timezone.utc).isoformat()
    must_change_password = False
    password_hash = None
    if data.password:
        password_hash = hash_password(data.password)
        must_change_password = False
    else:
        # Default behavior: auto-generate a temporary password for the student so
        # they can sign in and change it immediately. This matches the repo's
        # pattern of admin-created credentials with a secure hash.
        password_hash = hash_password(f"{data.student_id}-changeme")
        must_change_password = True

    doc_data = {
        "student_id": data.student_id,
        "name": data.name,
        "department": data.department,
        "batch": data.batch,
        "email": data.email,
        "password_hash": password_hash,
        "must_change_password": must_change_password,
        "is_active": True,
        "created_at": now,
    }

    doc_ref.set(doc_data)
    logger.info(f"Created student: {data.student_id} ({data.name})")

    # Check if face is enrolled
    face_enrolled = _check_face_enrolled(db, data.student_id)

    response = StudentResponse(
        **doc_data,
        face_enrolled=face_enrolled,
        must_change_password=must_change_password,
        temporary_password=(None if data.password else f"{data.student_id}-changeme"),
    )
    return response


async def get_student(student_id: str) -> StudentResponse:
    """Get a single student by their student_id."""
    db = get_db()
    doc = db.collection(STUDENTS_COLLECTION).document(student_id).get()

    if not doc.exists:
        raise NotFoundError("Student", student_id)

    data = doc.to_dict()

    face_enrolled = _check_face_enrolled(db, student_id)

    data.pop("face_enrolled", None)

    return StudentResponse(
        **data,
        face_enrolled=face_enrolled,
    )

async def list_students(
    department: str | None = None,
    batch: str | None = None,
    course_id: str | None = None,
) -> StudentListResponse:
    """
    List all students, optionally filtered by department, batch, or course.

    If course_id is provided, returns only students enrolled in that course.
    """
    db = get_db()

    # If filtering by course, look up enrollments first
    if course_id:
        return await _list_students_by_course(db, course_id)

    query = db.collection(STUDENTS_COLLECTION)

    if department:
        query = query.where("department", "==", department)
    if batch:
        query = query.where("batch", "==", batch)

    docs = query.get()
    students = []
    for doc in docs:
        data = doc.to_dict()
        face_enrolled = _check_face_enrolled(db, data["student_id"])
        data.pop("face_enrolled", None)
        students.append(StudentResponse(**data, face_enrolled=face_enrolled))

    return StudentListResponse(students=students, total=len(students))


async def get_student_courses_with_attendance(
    student_id: str,
) -> list[dict]:
    """Return the student's enrolled courses and per-session attendance."""
    db = get_db()
    enrollment_docs = (
        db.collection("enrollments")
        .where("student_id", "==", student_id)
        .get()
    )

    courses = []
    for enrollment_doc in enrollment_docs:
        enrollment = enrollment_doc.to_dict()
        course_id = enrollment["course_id"]
        course_doc = db.collection("courses").document(course_id).get()
        if not course_doc.exists:
            continue

        course = course_doc.to_dict()
        history = []
        present = 0
        late = 0
        absent = 0

        session_docs = (
            db.collection("attendance_sessions")
            .where("course_id", "==", course_id)
            .get()
        )
        for session_doc in session_docs:
            session = session_doc.to_dict()
            if session.get("status") == "cancelled":
                continue

            record_docs = (
                db.collection("attendance_records")
                .where("session_id", "==", session_doc.id)
                .where("student_id", "==", student_id)
                .limit(1)
                .get()
            )
            record = record_docs[0].to_dict() if record_docs else {}
            status = record.get("status", "absent")

            if status == "present":
                present += 1
            elif status == "late":
                late += 1
            else:
                absent += 1

            history.append({
                "session_id": session_doc.id,
                "session_date": session.get("session_date"),
                "start_time": session.get("start_time"),
                "end_time": session.get("end_time"),
                "status": status,
                "detected_at": record.get("detected_at"),
                "method": record.get("method"),
                "confidence": record.get("confidence"),
            })

        total_classes = len(history)
        courses.append({
            "course_id": course_id,
            "course_code": course.get("course_code", ""),
            "course_name": course.get("course_name", ""),
            "department": course.get("department", ""),
            "section": course.get("section", ""),
            "teacher_id": course.get("teacher_id", ""),
            "enrolled_at": enrollment.get("enrolled_at"),
            "total_classes": total_classes,
            "present": present,
            "late": late,
            "absent": absent,
            "percentage": round((present + late) / total_classes * 100, 1)
            if total_classes
            else 0.0,
            "attendance_history": history,
        })

    return courses


async def update_student(
    student_id: str, data: StudentUpdate
) -> StudentResponse:
    """Update student fields. Only provided fields are updated."""
    db = get_db()
    doc_ref = db.collection(STUDENTS_COLLECTION).document(student_id)

    if not doc_ref.get().exists:
        raise NotFoundError("Student", student_id)

    # Only update non-None fields
    update_data = data.model_dump(exclude_none=True)
    if update_data:
        doc_ref.update(update_data)
        logger.info(f"Updated student {student_id}: {list(update_data.keys())}")

    return await get_student(student_id)


async def delete_student(student_id: str) -> dict:
    """
    Soft-delete a student by setting is_active to False.

    Does not remove the document to preserve attendance history.
    """
    db = get_db()
    doc_ref = db.collection(STUDENTS_COLLECTION).document(student_id)

    if not doc_ref.get().exists:
        raise NotFoundError("Student", student_id)

    doc_ref.update({"is_active": False})
    logger.info(f"Soft-deleted student: {student_id}")

    return {"message": f"Student '{student_id}' has been deactivated."}


async def _list_students_by_course(db, course_id: str) -> StudentListResponse:
    """Get students enrolled in a specific course via the enrollments collection."""
    enrollment_docs = (
        db.collection("enrollments")
        .where("course_id", "==", course_id)
        .get()
    )

    student_ids = [doc.to_dict()["student_id"] for doc in enrollment_docs]

    students = []
    for sid in student_ids:
        try:
            student = await get_student(sid)
            students.append(student)
        except NotFoundError:
            logger.warning(f"Enrollment references missing student: {sid}")

    return StudentListResponse(students=students, total=len(students))


def _check_face_enrolled(db, student_id: str) -> bool:
    """Check if a student has a face embedding stored."""
    docs = (
        db.collection(FACE_EMBEDDINGS_COLLECTION)
        .where("student_id", "==", student_id)
        .limit(1)
        .get()
    )
    return len(docs) > 0
