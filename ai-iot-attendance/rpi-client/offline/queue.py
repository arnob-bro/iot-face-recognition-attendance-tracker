import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from api.client import NetworkError


class OfflineQueue:
    """SQLite-backed queue for attendance records that could not be synced immediately."""

    def __init__(self, db_path: str | None = None):
        db_file = db_path or str(Path(__file__).resolve().parent.parent / "attendance_queue.db")
        self.db_path = db_file
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                detected_at TEXT NOT NULL,
                confidence REAL,
                method TEXT DEFAULT 'face_recognition',
                synced INTEGER DEFAULT 0
            )
            """
        )
        self.conn.commit()

    def enqueue(self, session_id: str, student_id: str, detected_at: str | None = None, confidence: float = 0.0, method: str = "face_recognition") -> int:
        if detected_at is None:
            detected_at = datetime.now(timezone.utc).isoformat()

        cursor = self.conn.execute(
            "INSERT INTO queue (session_id, student_id, detected_at, confidence, method, synced) VALUES (?, ?, ?, ?, ?, 0)",
            (session_id, student_id, detected_at, confidence, method),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_pending(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM queue WHERE synced = 0 ORDER BY id ASC"
        ).fetchall()
        return [dict(row) for row in rows]

    def mark_synced(self, ids: list[int]) -> None:
        if not ids:
            return
        placeholders = ", ".join("?" for _ in ids)
        self.conn.execute(f"UPDATE queue SET synced = 1 WHERE id IN ({placeholders})", ids)
        self.conn.commit()

    def drain(self, api_client) -> list[dict]:
        pending = self.get_pending()
        if not pending:
            return []

        synced_records = []
        session_ids = {row["session_id"] for row in pending}
        for session_id in session_ids:
            session_rows = [row for row in pending if row["session_id"] == session_id]
            records = [
                {
                    "student_id": row["student_id"],
                    "confidence": float(row["confidence"] or 0.0),
                    "method": row["method"] or "face_recognition",
                }
                for row in session_rows
            ]
            try:
                synced_records.extend(api_client.sync_offline_records(session_id, records))
            except NetworkError as exc:
                if not exc.retryable:
                    self.mark_synced([row["id"] for row in session_rows])
                continue
            self.mark_synced([row["id"] for row in session_rows])
        return synced_records

    def close(self) -> None:
        self.conn.close()
