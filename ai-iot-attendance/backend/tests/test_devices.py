"""Tests for Raspberry Pi device assignment and session scoping."""


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

        session = client.post(
            "/api/v1/attendance/sessions",
            headers=auth_headers,
            json={"course_id": course_id, "device_id": "rpi-device-test"},
        )
        assert session.status_code == 201
        session_id = session.json()["session_id"]

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

        ended = client.put(
            f"/api/v1/attendance/sessions/{session_id}",
            headers=auth_headers,
            json={"status": "completed"},
        )
        assert ended.status_code == 200
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

        first = client.post(
            "/api/v1/attendance/sessions",
            headers=auth_headers,
            json={"course_id": course_one, "device_id": "rpi-device-conflict"},
        )
        assert first.status_code == 201
        second = client.post(
            "/api/v1/attendance/sessions",
            headers=auth_headers,
            json={"course_id": course_two, "device_id": "rpi-device-conflict"},
        )
        assert second.status_code == 409