"""
Tests for authentication endpoints.
"""

import pytest


class TestAuth:
    """Test the /api/v1/auth/* endpoints."""

    def test_login_success(self, client, admin_token):
        """Admin login should return a valid JWT token."""
        assert admin_token is not None
        assert len(admin_token) > 0

    def test_login_wrong_password(self, client):
        """Login with wrong password should return 401."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@test.edu", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Login with non-existent email should return 401."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@test.edu", "password": "whatever"},
        )
        assert response.status_code == 401

    def test_get_me(self, client, auth_headers):
        """GET /auth/me should return the current user's profile."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@test.edu"
        assert data["role"] == "admin"

    def test_get_me_no_token(self, client):
        """GET /auth/me without a token should return 403."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403

    def test_register_teacher(self, client, auth_headers):
        """Admin should be able to register a new teacher."""
        response = client.post(
            "/api/v1/auth/register",
            headers=auth_headers,
            json={
                "name": "Test Teacher",
                "email": "teacher@test.edu",
                "password": "teacherpass",
                "role": "teacher",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "teacher@test.edu"
        assert data["role"] == "teacher"

    def test_list_teachers_admin_full_access(self, client, auth_headers):
        """Admin should be able to view all teachers and admins."""
        response = client.post(
            "/api/v1/auth/register",
            headers=auth_headers,
            json={
                "name": "Second Teacher",
                "email": "teacher2@test.edu",
                "password": "teacherpass",
                "role": "teacher",
            },
        )
        assert response.status_code == 200

        response = client.get("/api/v1/auth/teachers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        emails = {item["email"] for item in data}
        assert "admin@test.edu" in emails
        assert "teacher@test.edu" in emails
        assert "teacher2@test.edu" in emails

    def test_teacher_has_partial_access_to_teacher_endpoints(self, client, auth_headers):
        """Teachers should only see their own profile and not other teachers."""
        response = client.post(
            "/api/v1/auth/register",
            headers=auth_headers,
            json={
                "name": "Restricted Teacher",
                "email": "teacher3@test.edu",
                "password": "teacherpass",
                "role": "teacher",
            },
        )
        assert response.status_code == 200

        teacher_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "teacher3@test.edu",
                "password": "teacherpass",
            },
        )
        assert teacher_login.status_code == 200
        teacher_token = teacher_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {teacher_token}"}

        list_response = client.get("/api/v1/auth/teachers", headers=headers)
        assert list_response.status_code == 200
        data = list_response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["email"] == "teacher3@test.edu"

        teacher_id = data[0]["teacher_id"]
        detail_response = client.get(
            f"/api/v1/auth/teachers/{teacher_id}",
            headers=headers,
        )
        assert detail_response.status_code == 200
        assert detail_response.json()["email"] == "teacher3@test.edu"

        other_teacher = client.get(
            "/api/v1/auth/teachers",
            headers=auth_headers,
        )
        other_teacher_id = next(
            item["teacher_id"]
            for item in other_teacher.json()
            if item["email"] == "teacher@test.edu"
        )

        forbidden = client.get(
            f"/api/v1/auth/teachers/{other_teacher_id}",
            headers=headers,
        )
        assert forbidden.status_code == 403
