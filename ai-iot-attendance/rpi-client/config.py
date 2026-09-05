from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings for the Raspberry Pi attendance client."""

    api_url: str = "http://localhost:8000"
    rpi_email: str = "admin@university.edu"
    rpi_password: str = "changeme123"
    course_id: str | None = None

    camera_index: int = 0
    camera_width: int = 640
    camera_height: int = 480
    camera_fps: int = 15

    esp32_serial_port: str = ""
    esp32_baud_rate: int = 115200

    face_match_threshold: float = 0.45
    attendance_cooldown_seconds: int = 60
    recognize_every_n_frames: int = 5

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
