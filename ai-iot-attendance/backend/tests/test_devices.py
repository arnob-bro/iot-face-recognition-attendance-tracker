"""Tests for Raspberry Pi device assignment and session scoping."""

import asyncio

import pytest

from app.core.exceptions import DuplicateError
from app.services import attendance_service


def _start_routine_session(course_id, routine_id, device_id):
    return asyncio.run(
        attendance_service.start_routine_session(
            {
                "course_id": course_id,
                "teacher_id": "device-test-teacher",
                "device_id": device_id,
            },
            routine_id,
        )
    )

def _create_course(client, headers, code):
    response = client.post(
        "/api/v1/courses/",
        headers=headers,
        json={
            "course_code": code,
            "course_name": "Device Test",
            "department": "CSE",
            "section": "A",
            "teacher_id": "device-test-teacher",
        },
    )
    assert response.status_code == 201
    return response.json()["course_id"]


class TestDevices:
    def test_device_session_lifecycle(self, client, auth_headers):
        device = client.post(
            "/api/v1/devices",
            headers=auth_headers,
            json={"device_id": "rpi-device-test", "name": "Test Pi", "location": "Lab"},
        )
        assert device.status_code == 201
        device_data = device.json()
        course_id = _create_course(client, auth_headers, "DEV101")

        session = _start_routine_session(
            course_id, "routine-device-test", "rpi-device-test"
        )
        session_id = session.session_id

        login = client.post(
            "/api/v1/devices/login",
            json={
                "device_id": "rpi-device-test",
                "device_secret": device_data["device_secret"],
            },
        )
        assert login.status_code == 200
        device_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        active = client.get(
            "/api/v1/attendance/sessions/active", headers=device_headers
        )
        assert active.status_code == 200
        assert active.json()["session_id"] == session_id

        record = client.post(
            f"/api/v1/attendance/sessions/{session_id}/record",
            headers=device_headers,
            json={"student_id": "unregistered-student", "confidence": 0.9},
        )
        assert record.status_code == 201

        asyncio.run(
            attendance_service.complete_routine_session(
                session_id, "routine-device-test"
            )
        )
        assert client.get(
            "/api/v1/attendance/sessions/active", headers=device_headers
        ).json() is None

    def test_one_active_session_per_device(self, client, auth_headers):
        device = client.post(
            "/api/v1/devices",
            headers=auth_headers,
            json={"device_id": "rpi-device-conflict", "name": "Conflict Pi"},
        )
        assert device.status_code == 201
        course_one = _create_course(client, auth_headers, "DEV201")
        course_two = _create_course(client, auth_headers, "DEV202")

        _start_routine_session(
            course_one, "routine-device-conflict-one", "rpi-device-conflict"
        )
        with pytest.raises(DuplicateError):
            _start_routine_session(
                course_two, "routine-device-conflict-two", "rpi-device-conflict"
            )