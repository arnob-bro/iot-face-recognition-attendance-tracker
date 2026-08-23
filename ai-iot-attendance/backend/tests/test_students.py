"""
Tests for student management endpoints.
"""

import pytest


class TestStudents:
    """Test the /api/v1/students/* endpoints."""

    def test_create_student(self, client, auth_headers):
        """Admin should be able to create a new student."""
        response = client.post(
            "/api/v1/students/",
            headers=auth_headers,
            json={
                "student_id": "20220104001",
                "name": "Test Student",
                "department": "CSE",
                "batch": "22",
                "email": "student001@test.edu",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["student_id"] == "20220104001"
        assert data["name"] == "Test Student"
        assert data["is_active"] is True
        assert data["face_enrolled"] is False

    def test_create_duplicate_student(self, client, auth_headers):
        """Creating a student with the same ID should return 409."""
        # First create
        client.post(
            "/api/v1/students/",
            headers=auth_headers,
            json={
                "student_id": "20220104002",
                "name": "Duplicate Student",
                "department": "CSE",
                "batch": "22",
                "email": "dup@test.edu",
            },
        )
        # Second create — should conflict
        response = client.post(
            "/api/v1/students/",
            headers=auth_headers,
            json={
                "student_id": "20220104002",
                "name": "Duplicate Student",
                "department": "CSE",
                "batch": "22",
                "email": "dup2@test.edu",
            },
        )
        assert response.status_code == 409

    def test_get_student(self, client, auth_headers):
        """Should retrieve a student by ID."""
        # Create first
        client.post(
            "/api/v1/students/",
            headers=auth_headers,
            json={
                "student_id": "20220104003",
                "name": "Get Test",
                "department": "EEE",
                "batch": "23",
                "email": "get@test.edu",
            },
        )

        response = client.get(
            "/api/v1/students/20220104003", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Get Test"
        assert data["department"] == "EEE"

    def test_get_nonexistent_student(self, client, auth_headers):
        """Getting a non-existent student should return 404."""
        response = client.get(
            "/api/v1/students/DOES_NOT_EXIST", headers=auth_headers
        )
        assert response.status_code == 404

    def test_update_student(self, client, auth_headers):
        """Should update specific fields of a student."""
        # Create first
        client.post(
            "/api/v1/students/",
            headers=auth_headers,
            json={
                "student_id": "20220104004",
                "name": "Before Update",
                "department": "CSE",
                "batch": "22",
                "email": "before@test.edu",
            },
        )

        response = client.put(
            "/api/v1/students/20220104004",
            headers=auth_headers,
            json={"name": "After Update"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "After Update"

    def test_delete_student(self, client, auth_headers):
        """Should soft-delete (deactivate) a student."""
        # Create first
        client.post(
            "/api/v1/students/",
            headers=auth_headers,
            json={
                "student_id": "20220104005",
                "name": "Delete Test",
                "department": "CSE",
                "batch": "22",
                "email": "del@test.edu",
            },
        )

        response = client.delete(
            "/api/v1/students/20220104005", headers=auth_headers
        )
        assert response.status_code == 200

        # Verify deactivated
        get_resp = client.get(
            "/api/v1/students/20220104005", headers=auth_headers
        )
        assert get_resp.json()["is_active"] is False

    def test_list_students(self, client, auth_headers):
        """Should return a list of students."""
        response = client.get("/api/v1/students/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "students" in data
        assert "total" in data

    def test_no_auth_returns_error(self, client):
        """Student endpoints without auth should return 403."""
        response = client.get("/api/v1/students/")
        assert response.status_code == 403
