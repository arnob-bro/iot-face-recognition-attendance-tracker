import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class NetworkError(RuntimeError):
    """Raised when the API cannot be reached."""

    def __init__(self, message: str, status_code: int | None = None, retryable: bool = True):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


class AttendanceAPIClient:
    """Synchronous API client for the Raspberry Pi face terminal."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None
        self.email: str | None = None
        self.password: str | None = None
        self.device_id: str | None = None
        self.device_secret: str | None = None
        self.client = httpx.Client(timeout=10.0)

    def login(self, email: str, password: str) -> str:
        self.email = email
        self.password = password
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

    def login_device(self, device_id: str, device_secret: str) -> str:
        self.device_id = device_id
        self.device_secret = device_secret
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/devices/login",
                json={"device_id": device_id, "device_secret": device_secret},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise NetworkError(
                f"Device login failed: HTTP {exc.response.status_code}",
                exc.response.status_code,
                retryable=False,
            ) from exc
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            raise NetworkError(f"Device login failed: {exc}") from exc

        payload = response.json()
        self.token = payload.get("access_token")
        if not self.token:
            raise NetworkError("Device login response did not include an access token.", retryable=False)
        return self.token

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        if self.token:
            headers.setdefault("Authorization", f"Bearer {self.token}")

        try:
            response = self.client.request(method, f"{self.base_url}{path}", headers=headers, **kwargs)
            if response.status_code == 401:
                if self.device_id is not None and self.device_secret is not None:
                    logger.warning("Device token expired; reauthenticating and retrying once.")
                    self.login_device(self.device_id, self.device_secret)
                    return self._request(method, path, **kwargs)
                if self.token is None or self.email is None or self.password is None:
                    raise NetworkError("Authentication required.")
                logger.warning("API token expired; reauthenticating and retrying once.")
                self.login(self.email, self.password)
                return self._request(method, path, **kwargs)
            if response.status_code >= 400:
                raise NetworkError(
                    f"API request failed ({method} {path}): HTTP {response.status_code}",
                    response.status_code,
                    retryable=response.status_code >= 500,
                )
            response.raise_for_status()
            return response
        except NetworkError:
            raise
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            raise NetworkError(f"API request failed ({method} {path}): {exc}") from exc

    def get_active_session(self) -> dict | None:
        params = {}
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
