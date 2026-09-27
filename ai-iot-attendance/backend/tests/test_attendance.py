"""
Tests for attendance session and recording endpoints.
"""

import asyncio
import pytest

from app.services import attendance_service


class TestAttendance:
    """Test the /api/v1/attendance/* endpoints."""

    def _start_routine_session(self, course_id):
        routine_id = f"routine-{course_id}"
        routine = {
            "course_id": course_id,
            "teacher_id": "test_teacher",
            "late_threshold_minutes": 15,
        }
        session = asyncio.run(
            attendance_service.start_routine_session(routine, routine_id)
        )
        return session.session_id, routine_id

    def _setup_course_and_student(self, client, auth_headers):
        """Helper: create a course and student for attendance testing."""
        # Create student
        client.post(
            "/api/v1/students/",
            headers=auth_headers,
            json={
                "student_id": "20220104099",
                "name": "Attendance Student",
                "department": "CSE",
                "batch": "22",
                "email": "att@test.edu",
            },
        )

        # Create course
        response = client.post(
            "/api/v1/courses/",
            headers=auth_headers,
            json={
                "course_code": "CSE4001",
                "course_name": "AI Lab",
                "department": "CSE",
                "section": "A",
                "teacher_id": "test_teacher",
            },
        )
        course_id = response.json().get("course_id", "")

        # Enroll student in course
        if course_id:
            client.post(
                f"/api/v1/courses/{course_id}/enroll",
                headers=auth_headers,
                json={
                    "student_id": "20220104099",
                    "course_id": course_id,
                },
            )

        return course_id

    def test_manual_session_lifecycle_routes_are_removed(self, client, auth_headers):
        assert client.post(
            "/api/v1/attendance/sessions",
            headers=auth_headers,
            json={"course_id": "course-1"},
        ).status_code == 405
        assert client.put(
            "/api/v1/attendance/sessions/session-1",
            headers=auth_headers,
            json={"status": "completed"},
        ).status_code == 405

    def test_record_attendance(self, client, auth_headers):
        """Should record a student's attendance in an active session."""
        course_id = self._setup_course_and_student(client, auth_headers)
        if not course_id:
            pytest.skip("Course creation failed")

        # Start session
        session_id, _ = self._start_routine_session(course_id)

        # Record attendance
        response = client.post(
            f"/api/v1/attendance/sessions/{session_id}/record",
            headers=auth_headers,
            json={
                "student_id": "20220104099",
                "confidence": 0.92,
                "method": "face",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["student_id"] == "20220104099"
        assert data["status"] in ("present", "late")

    def test_duplicate_attendance_prevention(self, client, auth_headers):
        """Recording the same student twice should return the existing record."""
        course_id = self._setup_course_and_student(client, auth_headers)
        if not course_id:
            pytest.skip("Course creation failed")

        # Start session
        session_id, _ = self._start_routine_session(course_id)

        # First record
        resp1 = client.post(
            f"/api/v1/attendance/sessions/{session_id}/record",
            headers=auth_headers,
            json={"student_id": "20220104099", "confidence": 0.92},
        )

        # Second record — same student
        resp2 = client.post(
            f"/api/v1/attendance/sessions/{session_id}/record",
            headers=auth_headers,
            json={"student_id": "20220104099", "confidence": 0.95},
        )

        # Both should succeed, second should return the existing record
        assert resp1.status_code == 201
        assert resp2.status_code == 201
        assert resp1.json()["record_id"] == resp2.json()["record_id"]

    def test_routine_completion_marks_absent_students(self, client, auth_headers):
        """Routine completion marks unrecorded students absent."""
        course_id = self._setup_course_and_student(client, auth_headers)
        if not course_id:
            pytest.skip("Course creation failed")

        # Start session
        session_id, routine_id = self._start_routine_session(course_id)
        completed = asyncio.run(
            attendance_service.complete_routine_session(session_id, routine_id)
        )
        assert completed.status == "completed"

    def test_health_check(self, client):
        """Health check should always succeed."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
