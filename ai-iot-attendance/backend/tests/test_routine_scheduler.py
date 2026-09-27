"""Unit tests for routine-driven attendance session scheduling."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from app.core.config import settings
from app.services import attendance_service, routine_scheduler


class FakeDocument:
    def __init__(self, document_id, data):
        self.id = document_id
        self.data = data

    def to_dict(self):
        return self.data


class FakeCollection:
    def __init__(self, documents):
        self.documents = documents

    def where(self, field, operator, value):
        assert operator == "=="
        return FakeCollection(
            [doc for doc in self.documents if doc.to_dict().get(field) == value]
        )

    def stream(self):
        return iter(self.documents)


class FakeDatabase:
    def __init__(self, routines, sessions):
        self.collections = {
            "class_routines": [
                FakeDocument(routine_id, data) for routine_id, data in routines
            ],
            "attendance_sessions": [
                FakeDocument(session_id, data) for session_id, data in sessions
            ],
        }

    def collection(self, name):
        return FakeCollection(self.collections[name])


def test_scheduler_starts_routine_inside_its_window(monkeypatch):
    now = datetime(2026, 9, 28, 9, 15, tzinfo=timezone.utc)
    routine = {
        "course_id": "course-1",
        "teacher_id": "teacher-1",
        "device_id": "rpi-1",
        "day_of_week": now.weekday(),
        "start_time": "09:00",
        "end_time": "10:00",
        "late_threshold_minutes": 10,
        "is_active": True,
    }
    start_session = AsyncMock()
    monkeypatch.setattr(settings, "routine_timezone", "UTC")
    monkeypatch.setattr(routine_scheduler, "get_db", lambda: FakeDatabase([("routine-1", routine)], []))
    monkeypatch.setattr(attendance_service, "start_routine_session", start_session)

    asyncio.run(routine_scheduler.process_routine_schedule(now))

    scheduled_routine, routine_id = start_session.await_args.args
    assert scheduled_routine["course_id"] == "course-1"
    assert scheduled_routine["device_id"] == "rpi-1"
    assert scheduled_routine["late_threshold_minutes"] == 10
    assert routine_id == "routine-1"


def test_scheduler_does_not_restart_a_cancelled_slot_same_day(monkeypatch):
    now = datetime(2026, 9, 28, 9, 15, tzinfo=timezone.utc)
    routine = {
        "course_id": "course-1",
        "teacher_id": "teacher-1",
        "day_of_week": now.weekday(),
        "start_time": "09:00",
        "end_time": "10:00",
        "is_active": True,
    }
    cancelled_session = {
        "course_id": "course-1",
        "routine_id": "routine-1",
        "status": "cancelled",
        "start_time": "2026-09-28T09:02:00+00:00",
    }
    start_session = AsyncMock()
    monkeypatch.setattr(settings, "routine_timezone", "UTC")
    monkeypatch.setattr(
        routine_scheduler,
        "get_db",
        lambda: FakeDatabase(
            [("routine-1", routine)], [("session-1", cancelled_session)]
        ),
    )
    monkeypatch.setattr(attendance_service, "start_routine_session", start_session)

    asyncio.run(routine_scheduler.process_routine_schedule(now))

    start_session.assert_not_awaited()


def test_scheduler_completes_overdue_session_after_restart(monkeypatch):
    now = datetime(2026, 9, 28, 9, 15, tzinfo=timezone.utc)
    routine = {
        "course_id": "course-1",
        "teacher_id": "teacher-1",
        "day_of_week": 6,
        "start_time": "09:00",
        "end_time": "10:00",
        "is_active": True,
    }
    active_session = {
        "course_id": "course-1",
        "routine_id": "routine-1",
        "status": "active",
        "start_time": "2026-09-27T09:05:00+00:00",
    }
    end_session = AsyncMock()
    monkeypatch.setattr(settings, "routine_timezone", "UTC")
    monkeypatch.setattr(
        routine_scheduler,
        "get_db",
        lambda: FakeDatabase(
            [("routine-1", routine)], [("session-1", active_session)]
        ),
    )
    monkeypatch.setattr(attendance_service, "complete_routine_session", end_session)

    asyncio.run(routine_scheduler.process_routine_schedule(now))

    session_id, routine_id = end_session.await_args.args
    assert session_id == "session-1"
    assert routine_id == "routine-1"