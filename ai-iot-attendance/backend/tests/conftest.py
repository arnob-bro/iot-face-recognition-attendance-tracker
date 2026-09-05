"""
Test fixtures and configuration for pytest.

Sets up a test client using FastAPI's TestClient and
configures Firebase emulator for isolated testing.
"""

import os
import pytest
from fastapi.testclient import TestClient

# Point to Firebase Emulator for testing (if available)
os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8080")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("ADMIN_EMAIL", "admin@test.edu")
os.environ.setdefault("ADMIN_PASSWORD", "testpass123")
os.environ.setdefault("ADMIN_NAME", "Test Admin")


def _reset_firestore_collections():
    """Ensure a clean emulator state before the test session starts."""
    from app.core.firebase import init_firebase, get_db

    init_firebase()
    db = get_db()
    for collection_name in [
        "teachers",
        "students",
        "courses",
        "enrollments",
        "attendance_sessions",
        "attendance_records",
        "face_embeddings",
    ]:
        docs = db.collection(collection_name).stream()
        for doc in docs:
            doc.reference.delete()


@pytest.fixture(scope="session")
def client():
    """
    Create a FastAPI test client.

    Uses the same app instance, including lifespan (Firebase init).
    Scoped to the entire test session for efficiency.
    """
    _reset_firestore_collections()

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_token(client):
    """
    Get a JWT token for the admin user.

    The admin is bootstrapped during app startup via lifespan.
    """
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": os.environ["ADMIN_EMAIL"],
            "password": os.environ["ADMIN_PASSWORD"],
        },
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    # If login fails (e.g., no Firebase), skip tests gracefully
    pytest.skip("Could not authenticate admin — Firebase may not be available.")


@pytest.fixture
def auth_headers(admin_token):
    """Convenience fixture for authenticated request headers."""
    return {"Authorization": f"Bearer {admin_token}"}
