"""
Student service — CRUD operations for students in Firebase.

Students are stored in the 'students' collection keyed by their
university-issued student_id (e.g., "20220104064").
"""

import logging
from datetime import datetime, timezone

from app.core.firebase import get_db
from app.core.exceptions import NotFoundError, DuplicateError
from app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentListResponse,
)

logger = logging.getLogger(__name__)

STUDENTS_COLLECTION = "students"
FACE_EMBEDDINGS_COLLECTION = "face_embeddings"


async def create_student(data: StudentCreate) -> StudentResponse:
    """Create a new student. Uses student_id as the document ID."""
    db = get_db()

    # Check for duplicate student_id
    doc_ref = db.collection(STUDENTS_COLLECTION).document(data.student_id)
    if doc_ref.get().exists:
        raise DuplicateError("Student", data.student_id)

    now = datetime.now(timezone.utc).isoformat()
    doc_data = {
        "student_id": data.student_id,
        "name": data.name,
        "department": data.department,
        "batch": data.batch,
        "email": data.email,
        "is_active": True,
        "created_at": now,
    }

    doc_ref.set(doc_data)
    logger.info(f"Created student: {data.student_id} ({data.name})")

    # Check if face is enrolled
    face_enrolled = _check_face_enrolled(db, data.student_id)

    return StudentResponse(
        **doc_data,
        face_enrolled=face_enrolled,
    )


async def get_student(student_id: str) -> StudentResponse:
    """Get a single student by their student_id."""
    db = get_db()
    doc = db.collection(STUDENTS_COLLECTION).document(student_id).get()

    if not doc.exists:
        raise NotFoundError("Student", student_id)

    data = doc.to_dict()
    face_enrolled = _check_face_enrolled(db, student_id)
    data.pop("face_enrolled", None)

    return StudentResponse(**data, face_enrolled=face_enrolled)


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
