"""
Course service — CRUD operations for courses and student enrollments.

Courses are stored with auto-generated IDs in the 'courses' collection.
Enrollments link students to courses (many-to-many).
"""

import logging
from datetime import datetime, timezone

from app.core.firebase import get_db
from app.core.exceptions import NotFoundError, DuplicateError
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseListResponse,
    EnrollmentCreate,
    EnrollmentResponse,
)

logger = logging.getLogger(__name__)

COURSES_COLLECTION = "courses"
ENROLLMENTS_COLLECTION = "enrollments"


async def create_course(data: CourseCreate) -> CourseResponse:
    """Create a new course."""
    db = get_db()

    # Check for duplicate course_code + section combo
    existing = (
        db.collection(COURSES_COLLECTION)
        .where("course_code", "==", data.course_code)
        .where("section", "==", data.section)
        .limit(1)
        .get()
    )
    if existing:
        raise DuplicateError("Course", f"{data.course_code}-{data.section}")

    now = datetime.now(timezone.utc).isoformat()
    doc_data = {
        "course_code": data.course_code,
        "course_name": data.course_name,
        "department": data.department,
        "section": data.section,
        "teacher_id": data.teacher_id,
        "total_classes": 0,
        "created_at": now,
    }

    doc_ref = db.collection(COURSES_COLLECTION).add(doc_data)
    course_id = doc_ref[1].id

    logger.info(f"Created course: {data.course_code} section {data.section}")

    return CourseResponse(course_id=course_id, **doc_data)


async def get_course(course_id: str) -> CourseResponse:
    """Get a single course by its ID."""
    db = get_db()
    doc = db.collection(COURSES_COLLECTION).document(course_id).get()

    if not doc.exists:
        raise NotFoundError("Course", course_id)

    data = doc.to_dict()
    return CourseResponse(course_id=doc.id, **data)


async def list_courses(
    teacher_id: str | None = None,
    department: str | None = None,
) -> CourseListResponse:
    """List all courses, optionally filtered by teacher or department."""
    db = get_db()
    query = db.collection(COURSES_COLLECTION)

    if teacher_id:
        query = query.where("teacher_id", "==", teacher_id)
    if department:
        query = query.where("department", "==", department)

    docs = query.get()
    courses = [
        CourseResponse(course_id=doc.id, **doc.to_dict())
        for doc in docs
    ]

    return CourseListResponse(courses=courses, total=len(courses))


async def update_course(
    course_id: str, data: CourseUpdate
) -> CourseResponse:
    """Update course fields."""
    db = get_db()
    doc_ref = db.collection(COURSES_COLLECTION).document(course_id)

    if not doc_ref.get().exists:
        raise NotFoundError("Course", course_id)

    update_data = data.model_dump(exclude_none=True)
    if update_data:
        doc_ref.update(update_data)
        logger.info(f"Updated course {course_id}: {list(update_data.keys())}")

    return await get_course(course_id)


async def delete_course(course_id: str) -> dict:
    """Delete a course and its enrollments."""
    db = get_db()
    doc_ref = db.collection(COURSES_COLLECTION).document(course_id)

    if not doc_ref.get().exists:
        raise NotFoundError("Course", course_id)

    # Delete associated enrollments
    enrollment_docs = (
        db.collection(ENROLLMENTS_COLLECTION)
        .where("course_id", "==", course_id)
        .get()
    )
    for edoc in enrollment_docs:
        edoc.reference.delete()

    doc_ref.delete()
    logger.info(f"Deleted course: {course_id}")

    return {"message": f"Course '{course_id}' has been deleted."}


async def enroll_student(data: EnrollmentCreate) -> EnrollmentResponse:
    """Enroll a student in a course."""
    db = get_db()

    # Verify course exists
    course_doc = db.collection(COURSES_COLLECTION).document(data.course_id).get()
    if not course_doc.exists:
        raise NotFoundError("Course", data.course_id)

    # Verify student exists
    student_doc = db.collection("students").document(data.student_id).get()
    if not student_doc.exists:
        raise NotFoundError("Student", data.student_id)

    # Check for duplicate enrollment
    existing = (
        db.collection(ENROLLMENTS_COLLECTION)
        .where("student_id", "==", data.student_id)
        .where("course_id", "==", data.course_id)
        .limit(1)
        .get()
    )
    if existing:
        raise DuplicateError(
            "Enrollment",
            f"{data.student_id} in {data.course_id}",
        )

    now = datetime.now(timezone.utc).isoformat()
    doc_data = {
        "student_id": data.student_id,
        "course_id": data.course_id,
        "enrolled_at": now,
    }

    doc_ref = db.collection(ENROLLMENTS_COLLECTION).add(doc_data)
    enrollment_id = doc_ref[1].id

    logger.info(
        f"Enrolled student {data.student_id} in course {data.course_id}"
    )

    return EnrollmentResponse(enrollment_id=enrollment_id, **doc_data)


async def unenroll_student(student_id: str, course_id: str) -> dict:
    """Remove a student's enrollment from a course."""
    db = get_db()

    docs = (
        db.collection(ENROLLMENTS_COLLECTION)
        .where("student_id", "==", student_id)
        .where("course_id", "==", course_id)
        .limit(1)
        .get()
    )

    if not docs:
        raise NotFoundError("Enrollment", f"{student_id} in {course_id}")

    docs[0].reference.delete()
    logger.info(f"Unenrolled student {student_id} from course {course_id}")

    return {"message": f"Student '{student_id}' unenrolled from course '{course_id}'."}


async def get_course_students(course_id: str) -> list[dict]:
    """Get all students enrolled in a specific course."""
    db = get_db()

    # Verify course exists
    course_doc = db.collection(COURSES_COLLECTION).document(course_id).get()
    if not course_doc.exists:
        raise NotFoundError("Course", course_id)

    enrollment_docs = (
        db.collection(ENROLLMENTS_COLLECTION)
        .where("course_id", "==", course_id)
        .get()
    )

    students = []
    for edoc in enrollment_docs:
        edata = edoc.to_dict()
        student_doc = db.collection("students").document(edata["student_id"]).get()
        if student_doc.exists:
            sdata = student_doc.to_dict()
            students.append({
                "student_id": edata["student_id"],
                "name": sdata.get("name", ""),
                "department": sdata.get("department", ""),
                "batch": sdata.get("batch", ""),
            })

    return students
