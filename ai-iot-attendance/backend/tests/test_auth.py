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
