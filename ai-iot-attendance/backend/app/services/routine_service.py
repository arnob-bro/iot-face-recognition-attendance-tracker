"""Class routine service for schedule-based session automation."""

import logging
from datetime import datetime, timezone

from app.core.exceptions import DuplicateError, NotFoundError, ValidationError
from app.core.firebase import get_db

logger = logging.getLogger(__name__)

ROUTINES_COLLECTION = "class_routines"
SESSIONS_COLLECTION = "attendance_sessions"


async def list_routines(teacher_id: str | None = None) -> list[dict]:
    """List routines, optionally filtered to a teacher."""
    db = get_db()
    query = db.collection(ROUTINES_COLLECTION)
    if teacher_id:
        query = query.where("teacher_id", "==", teacher_id)
    docs = query.get()
    return [doc.to_dict() | {"routine_id": doc.id} for doc in docs]


async def get_routine(routine_id: str) -> dict:
    db = get_db()
    doc = db.collection(ROUTINES_COLLECTION).document(routine_id).get()
    if not doc.exists:
        raise NotFoundError("Routine", routine_id)
    data = doc.to_dict()
    data["routine_id"] = doc.id
    return data


async def create_routine(data: dict) -> dict:
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()

    _validate_no_overlap(db, data)

    payload = {
        "course_id": data["course_id"],
        "teacher_id": data["teacher_id"],
        "device_id": data.get("device_id"),
        "room": data.get("room"),
        "day_of_week": int(data["day_of_week"]),
        "start_time": data["start_time"],
        "end_time": data["end_time"],
        "late_threshold_minutes": int(data.get("late_threshold_minutes", 15)),
        "is_active": data.get("is_active", True),
        "created_at": now,
        "updated_at": now,
    }
    ref = db.collection(ROUTINES_COLLECTION).add(payload)
    routine_id = ref[1].id
    payload["routine_id"] = routine_id
    return payload


async def update_routine(routine_id: str, data: dict) -> dict:
    db = get_db()
    ref = db.collection(ROUTINES_COLLECTION).document(routine_id)
    doc = ref.get()
    if not doc.exists:
        raise NotFoundError("Routine", routine_id)

    current = doc.to_dict()
    merged = {**current, **data}
    _validate_no_overlap(db, merged, ignore_routine_id=routine_id)
    merged["updated_at"] = datetime.now(timezone.utc).isoformat()
    ref.update(merged)
    merged["routine_id"] = routine_id
    return merged


async def delete_routine(routine_id: str) -> dict:
    db = get_db()
    ref = db.collection(ROUTINES_COLLECTION).document(routine_id)
    if not ref.get().exists:
        raise NotFoundError("Routine", routine_id)
    ref.delete()
    return {"message": f"Routine '{routine_id}' deleted."}


def _validate_no_overlap(db, data: dict, ignore_routine_id: str | None = None) -> None:
    """Reject overlapping routines for the same teacher or device/room on a day."""
    day = int(data["day_of_week"])
    start = data["start_time"]
    end = data["end_time"]
    teacher_id = data.get("teacher_id")
    device_id = data.get("device_id")
    room = data.get("room")

    if teacher_id:
        query = db.collection(ROUTINES_COLLECTION).where("teacher_id", "==", teacher_id).where("day_of_week", "==", day)
        docs = query.get()
        for doc in docs:
            if doc.id == ignore_routine_id:
                continue
            current = doc.to_dict()
            if _ranges_overlap(start, end, current.get("start_time"), current.get("end_time")):
                raise DuplicateError("Routine overlap", f"teacher {teacher_id} on day {day}")

    if device_id or room:
        query = db.collection(ROUTINES_COLLECTION)
        if device_id:
            query = query.where("device_id", "==", device_id)
        elif room:
            query = query.where("room", "==", room)
        docs = query.get()
        for doc in docs:
            if doc.id == ignore_routine_id:
                continue
            current = doc.to_dict()
            if int(current.get("day_of_week")) != day:
                continue
            if _ranges_overlap(start, end, current.get("start_time"), current.get("end_time")):
                target = device_id or room or "room"
                raise DuplicateError("Routine overlap", f"device/room {target} on day {day}")


def _ranges_overlap(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
    """Return True if two HH:MM ranges overlap."""
    if not start_a or not end_a or not start_b or not end_b:
        return False
    try:
        a_start = datetime.strptime(start_a, "%H:%M").time()
        a_end = datetime.strptime(end_a, "%H:%M").time()
        b_start = datetime.strptime(start_b, "%H:%M").time()
        b_end = datetime.strptime(end_b, "%H:%M").time()
    except ValueError:
        raise ValidationError("Routine times must be in HH:MM format.")
    return not (a_end <= b_start or b_end <= a_start)


async def get_due_routines(now: datetime | None = None) -> list[dict]:
    """Return routines that should start or end at the current time."""
    db = get_db()
    if now is None:
        now = datetime.now(timezone.utc)

    day = now.weekday()
    time_now = now.strftime("%H:%M")
    docs = db.collection(ROUTINES_COLLECTION).where("day_of_week", "==", day).where("is_active", "==", True).get()
    due = []
    for doc in docs:
        data = doc.to_dict()
        if data.get("start_time") == time_now:
            due.append({"kind": "start", "routine_id": doc.id, **data})
        if data.get("end_time") == time_now:
            due.append({"kind": "end", "routine_id": doc.id, **data})
    return due


async def _has_active_session_for_routine(db, course_id: str, routine_id: str | None = None) -> bool:
    query = db.collection(SESSIONS_COLLECTION).where("course_id", "==", course_id).where("status", "==", "active")
    if routine_id:
        query = query.where("routine_id", "==", routine_id)
    return len(query.get()) > 0
