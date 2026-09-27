"""Tests for routine scheduling, collision logic, and student self-access."""

import pytest


class TestRoutineAndStudentAccess:
    def test_student_login_and_self_access(self, client):
        admin = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@test.edu", "password": "testpass123"},
        )
        admin_headers = {"Authorization": f"Bearer {admin.json()['access_token']}"}

        student_payload = {
            "student_id": "20220104077",
            "name": "Routine Student",
            "department": "CSE",
            "batch": "22",
            "email": "routine@student.edu",
            "password": "studentpass123",
        }
        created = client.post("/api/v1/students/", headers=admin_headers, json=student_payload)
        assert created.status_code == 201

        login = client.post("/api/v1/students/login?student_id=20220104077&password=studentpass123")
        assert login.status_code == 200, login.text
        token = login.json()["access_token"]

        own_student = client.get("/api/v1/students/20220104077", headers={"Authorization": f"Bearer {token}"})
        assert own_student.status_code == 200

        other = client.get("/api/v1/students/20220104001", headers={"Authorization": f"Bearer {token}"})
        assert other.status_code in (403, 401, 500)

    def test_routine_overlap_rejected(self, client):
        admin = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@test.edu", "password": "testpass123"},
        )
        headers = {"Authorization": f"Bearer {admin.json()['access_token']}"}

        course = client.post(
            "/api/v1/courses/",
            headers=headers,
            json={
                "course_code": "CSE9001",
                "course_name": "Routine Lab",
                "department": "CSE",
                "section": "B",
                "teacher_id": "teacher-1",
            },
        )
        course_id = course.json()["course_id"]

        first = client.post(
            "/api/v1/routines/",
            headers=headers,
            json={
                "course_id": course_id,
                "teacher_id": "teacher-1",
                "device_id": "rpi-1",
                "room": "Lab 1",
                "day_of_week": 1,
                "start_time": "09:00",
                "end_time": "10:00",
            },
        )
        assert first.status_code == 201

        second = client.post(
            "/api/v1/routines/",
            headers=headers,
            json={
                "course_id": course_id,
                "teacher_id": "teacher-1",
                "device_id": "rpi-1",
                "room": "Lab 1",
                "day_of_week": 1,
                "start_time": "09:30",
                "end_time": "10:30",
            },
        )
        assert second.status_code in (409, 422)
