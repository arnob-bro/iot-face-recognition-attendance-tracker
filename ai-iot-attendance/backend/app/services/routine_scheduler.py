"""Background processing for routine-driven attendance sessions."""

import asyncio
import logging
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.core.firebase import get_db
from app.services import attendance_service

logger = logging.getLogger(__name__)

ROUTINES_COLLECTION = "class_routines"
SESSIONS_COLLECTION = "attendance_sessions"


def _parse_time(value: str) -> time:
    return datetime.strptime(value, "%H:%M").time()


def _session_local_date(session: dict, timezone_info: ZoneInfo):
    start_time = session.get("start_time")
    if not start_time:
        return None
    try:
        started_at = datetime.fromisoformat(start_time)
    except (TypeError, ValueError):
        return None
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    return started_at.astimezone(timezone_info).date()


async def process_routine_schedule(now: datetime | None = None) -> None:
    """Start due routine sessions and complete routine sessions past their end time."""
    timezone_info = ZoneInfo(settings.routine_timezone)
    current = now or datetime.now(timezone_info)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone_info)
    current = current.astimezone(timezone_info)
    db = get_db()

    for routine_doc in db.collection(ROUTINES_COLLECTION).stream():
        routine = routine_doc.to_dict() or {}
        routine_id = routine_doc.id

        try:
            routine_day = int(routine.get("day_of_week", -1))
            start_time = _parse_time(routine.get("start_time", ""))
            end_time = _parse_time(routine.get("end_time", ""))
        except (TypeError, ValueError):
            logger.warning("Skipping routine %s with an invalid weekday or time", routine_id)
            continue

        if end_time <= start_time:
            logger.warning("Skipping routine %s with a non-positive time window", routine_id)
            continue

        sessions = [
            session_doc.to_dict() | {"session_id": session_doc.id}
            for session_doc in db.collection(SESSIONS_COLLECTION)
            .where("routine_id", "==", routine_id)
            .stream()
        ]
        sessions = [
            session
            for session in sessions
            if session.get("course_id") == routine.get("course_id")
        ]

        active_sessions = [
            session for session in sessions if session.get("status") == "active"
        ]
        for session in active_sessions:
            session_date = _session_local_date(session, timezone_info)
            if session_date is None:
                continue
            scheduled_end = datetime.combine(
                session_date, end_time, tzinfo=timezone_info
            )
            if current >= scheduled_end:
                try:
                    await attendance_service.complete_routine_session(
                        session["session_id"], routine_id
                    )
                    logger.info(
                        "Routine %s completed attendance session %s",
                        routine_id,
                        session["session_id"],
                    )
                except Exception:
                    logger.exception(
                        "Could not complete routine session %s", session["session_id"]
                    )

        if routine_day != current.weekday():
            continue

        if not routine.get("is_active", True) or current.time() < start_time:
            continue
        if current.time() >= end_time:
            continue
        if active_sessions:
            continue

        already_closed_today = any(
            session.get("status") in ("completed", "cancelled")
            and _session_local_date(session, timezone_info) == current.date()
            for session in sessions
        )
        if already_closed_today:
            logger.info(
                "Skipping routine %s because a session for today's slot is already closed",
                routine_id,
            )
            continue

        try:
            await attendance_service.start_routine_session(routine, routine_id)
            logger.info("Started attendance session for routine %s", routine_id)
        except Exception:
            # The attendance service's central guard rejects collisions with any active session.
            logger.exception("Could not start attendance session for routine %s", routine_id)


async def run_routine_scheduler(stop_event: asyncio.Event) -> None:
    """Poll routine schedules until the application lifespan requests shutdown."""
    interval = max(1, settings.routine_scheduler_interval_seconds)
    logger.info(
        "Routine scheduler started (timezone=%s, interval=%ss)",
        settings.routine_timezone,
        interval,
    )
    while not stop_event.is_set():
        try:
            await process_routine_schedule()
        except Exception:
            logger.exception("Routine scheduler tick failed")

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except TimeoutError:
            pass

    logger.info("Routine scheduler stopped")