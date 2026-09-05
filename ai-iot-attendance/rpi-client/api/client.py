import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class NetworkError(RuntimeError):
    """Raised when the API cannot be reached."""


class AttendanceAPIClient:
    """Synchronous API client for the Raspberry Pi face terminal."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None
        self.client = httpx.Client(timeout=10.0)

    def login(self, email: str, password: str) -> str:
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"email": email, "password": password},
            )
            response.raise_for_status()
        except (httpx.HTTPError, httpx.TimeoutException, httpx.ConnectError) as exc:
            raise NetworkError(f"Login failed: {exc}") from exc

        payload = response.json()
        self.token = payload.get("access_token")
        if not self.token:
            raise NetworkError("Login response did not include an access token.")
        return self.token

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        if self.token:
            headers.setdefault("Authorization", f"Bearer {self.token}")

        try:
            response = self.client.request(method, f"{self.base_url}{path}", headers=headers, **kwargs)
            if response.status_code == 401:
                if self.token is None:
                    raise NetworkError("Authentication required.")
                logger.warning("API token expired; reauthenticating and retrying once.")
                self.token = None
                return self._request(method, path, **kwargs)
            response.raise_for_status()
            return response
        except (httpx.HTTPError, httpx.TimeoutException, httpx.ConnectError) as exc:
            raise NetworkError(f"API request failed ({method} {path}): {exc}") from exc

    def get_active_session(self, course_id: str | None = None) -> dict | None:
        params = {}
        if course_id:
            params["course_id"] = course_id
        response = self._request("GET", "/api/v1/attendance/sessions/active", params=params)
        data = response.json()
        return data if data else None

    def recognize_face(self, jpeg_bytes: bytes) -> dict:
        files = {"file": ("frame.jpg", jpeg_bytes, "image/jpeg")}
        response = self._request("POST", "/api/v1/faces/recognize", files=files)
        return response.json()

    def record_attendance(self, session_id: str, student_id: str, confidence: float, method: str = "face_recognition") -> dict:
        response = self._request(
            "POST",
            f"/api/v1/attendance/sessions/{session_id}/record",
            json={
                "student_id": student_id,
                "confidence": confidence,
                "method": method,
            },
        )
        return response.json()

    def sync_offline_records(self, session_id: str, records: list[dict]) -> list[dict]:
        response = self._request(
            "POST",
            f"/api/v1/attendance/sessions/{session_id}/sync",
            json={"records": records},
        )
        return response.json()

    def close(self) -> None:
        self.client.close()
