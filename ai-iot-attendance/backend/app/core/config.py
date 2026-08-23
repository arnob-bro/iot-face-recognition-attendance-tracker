"""
Application configuration — re-exported from core package.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # --- Firebase ---
    firebase_project_id: str = "demo-project"
    firebase_credentials_path: str = "./firebase-credentials.json"

    # --- Authentication ---
    jwt_secret_key: str = "CHANGE-THIS-IN-PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 480

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # --- AI / Face Recognition ---
    face_match_threshold: float = 0.45
    liveness_enabled: bool = True
    use_mock_ai: bool = True
    model_dir: str = "./models"

    # --- Attendance ---
    attendance_cooldown_seconds: int = 60
    late_threshold_minutes: int = 15

    # --- Camera ---
    camera_index: int = 0
    camera_width: int = 640
    camera_height: int = 480
    camera_fps: int = 15

    # --- ESP32 ---
    esp32_serial_port: str = "/dev/ttyUSB0"
    esp32_baud_rate: int = 115200

    # --- Admin Bootstrap ---
    admin_email: str = "admin@university.edu"
    admin_password: str = "changeme123"
    admin_name: str = "System Administrator"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


settings = Settings()
