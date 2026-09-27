"""Seed deterministic mock records into the backend's Firestore collections.

Run from ``backend/``. By default this script only permits a Firestore emulator.
Optional face images are grouped by student ID and embedded with the real
InsightFace detector and recognizer.
"""

import argparse
import hashlib
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from app.ai.embeddings.utils import calculate_representative_embedding, encode_embedding
from app.core.firebase import close_firebase, get_db, init_firebase
from app.core.security import hash_password

logger = logging.getLogger("mock_data")

MOCK_ADMIN_PASSWORD = "MockAdmin-Only-123!"
MOCK_TEACHER_PASSWORD = "MockTeacher-Only-123!"
MOCK_DEVICE_SECRET = "mock-device-secret-do-not-use-in-production"


def _mock_documents(now: datetime) -> dict[str, dict[str, dict]]:
    """Build related documents for each collection using stable document IDs."""
    created_at = now.isoformat()
    old_created_at = (now - timedelta(days=90)).isoformat()

    teachers = {
        "mock-admin": {
            "name": "Mock Administrator",
            "email": "mock.admin@example.test",
            "password_hash": hash_password(MOCK_ADMIN_PASSWORD),
            "role": "admin",
            "created_at": old_created_at,
        },
        "mock-teacher-01": {
            "name": "Taylor Morgan",
            "email": "taylor.morgan@example.test",
            "password_hash": hash_password(MOCK_TEACHER_PASSWORD),
            "role": "teacher",
            "created_at": old_created_at,
        },
    }

    student_specs = [
        ("MOCK001", "Avery Chen", "Computer Science", "2024", "avery.chen@example.test", "MockStudent-001!"),
        ("MOCK002", "Jordan Patel", "Computer Science", "2024", "jordan.patel@example.test", "MockStudent-002!"),
        ("MOCK003", "Riley Okafor", "Electrical Engineering", "2023", "riley.okafor@example.test", "MockStudent-003!"),
    ]
    students = {
        student_id: {
            "student_id": student_id,
            "name": name,
            "department": department,
            "batch": batch,
            "email": email,
            "password_hash": hash_password(password),
            "must_change_password": False,
            "is_active": True,
            "created_at": old_created_at,
        }
        for student_id, name, department, batch, email, password in student_specs
    }

    courses = {
        "mock-course-cs101": {
            "course_code": "MOCK-CS101",
            "course_name": "Introduction to Computing",
            "department": "Computer Science",
            "section": "A",
            "teacher_id": "mock-teacher-01",
            "total_classes": 1,
            "created_at": old_created_at,
        },
        "mock-course-ee201": {
            "course_code": "MOCK-EE201",
            "course_name": "Circuits and Systems",
            "department": "Electrical Engineering",
            "section": "B",
            "teacher_id": "mock-teacher-01",
            "total_classes": 1,
            "created_at": old_created_at,
        },
    }

    enrollments = {
        "mock-enrollment-cs101-001": {
            "student_id": "MOCK001",
            "course_id": "mock-course-cs101",
            "enrolled_at": old_created_at,
        },
        "mock-enrollment-cs101-002": {
            "student_id": "MOCK002",
            "course_id": "mock-course-cs101",
            "enrolled_at": old_created_at,
        },
        "mock-enrollment-cs101-003": {
            "student_id": "MOCK003",
            "course_id": "mock-course-cs101",
            "enrolled_at": old_created_at,
        },
        "mock-enrollment-ee201-002": {
            "student_id": "MOCK002",
            "course_id": "mock-course-ee201",
            "enrolled_at": old_created_at,
        },
        "mock-enrollment-ee201-003": {
            "student_id": "MOCK003",
            "course_id": "mock-course-ee201",
            "enrolled_at": old_created_at,
        },
    }

    devices = {
        "mock-rpi-01": {
            "name": "Mock Raspberry Pi 01",
            "location": "Mock Lab A",
            "secret_hash": hash_password(MOCK_DEVICE_SECRET),
            "enabled": True,
            "last_seen_at": None,
        }
    }

    routine_specs = [
        ("mock-routine-cs101", "mock-course-cs101", "Mock Lab A", "09:00", "10:00"),
        ("mock-routine-ee201", "mock-course-ee201", "Mock Lab B", "11:00", "12:00"),
    ]
    routines = {
        routine_id: {
            "course_id": course_id,
            "teacher_id": "mock-teacher-01",
            "device_id": "mock-rpi-01" if course_id.endswith("cs101") else None,
            "room": room,
            "day_of_week": now.weekday(),
            "start_time": start_time,
            "end_time": end_time,
            "late_threshold_minutes": 15,
            "is_active": False,
            "created_at": old_created_at,
            "updated_at": created_at,
        }
        for routine_id, course_id, room, start_time, end_time in routine_specs
    }

    session_specs = [
        (
            "mock-session-cs101",
            "mock-course-cs101",
            "mock-routine-cs101",
            now - timedelta(days=1),
        ),
        (
            "mock-session-ee201",
            "mock-course-ee201",
            "mock-routine-ee201",
            now - timedelta(days=2),
        ),
    ]
    sessions = {}
    for session_id, course_id, routine_id, started_at in session_specs:
        sessions[session_id] = {
            "course_id": course_id,
            "teacher_id": "mock-teacher-01",
            "session_date": started_at.strftime("%Y-%m-%d"),
            "start_time": started_at.isoformat(),
            "end_time": (started_at + timedelta(hours=1)).isoformat(),
            "late_threshold_minutes": 15,
            "status": "completed",
            "device_id": "mock-rpi-01" if course_id.endswith("cs101") else None,
            "source": "routine",
            "routine_id": routine_id,
        }

    attendance_specs = [
        ("mock-session-cs101", "MOCK001", "present", 0.96, "face", 4),
        ("mock-session-cs101", "MOCK002", "late", 0.89, "face", 22),
        ("mock-session-cs101", "MOCK003", "absent", 0.0, "auto", 60),
        ("mock-session-ee201", "MOCK002", "present", 0.94, "face", 3),
        ("mock-session-ee201", "MOCK003", "absent", 0.0, "auto", 60),
    ]
    attendance_records = {}
    for session_id, student_id, status, confidence, method, minute_offset in attendance_specs:
        record_key = hashlib.sha256(
            f"{session_id}:{student_id}".encode("utf-8")
        ).hexdigest()
        session_start = next(
            started_at
            for candidate_id, _, _, started_at in session_specs
            if candidate_id == session_id
        )
        student = students[student_id]
        attendance_records[record_key] = {
            "session_id": session_id,
            "student_id": student_id,
            "student_name": student["name"],
            "status": status,
            "confidence": confidence,
            "detected_at": (session_start + timedelta(minutes=minute_offset)).isoformat(),
            "method": method,
        }

    return {
        "teachers": teachers,
        "students": students,
        "courses": courses,
        "enrollments": enrollments,
        "rpi_devices": devices,
        "class_routines": routines,
        "attendance_sessions": sessions,
        "attendance_records": attendance_records,
        "face_embeddings": {},
    }


def _student_id_for_image(path: Path, directory: Path, student_ids: set[str]) -> str | None:
    relative_parts = path.relative_to(directory).parts
    if len(relative_parts) > 1 and relative_parts[0] in student_ids:
        return relative_parts[0]

    filename = path.stem
    candidates = [
        student_id
        for student_id in student_ids
        if filename == student_id
        or filename.startswith(f"{student_id}_")
        or filename.startswith(f"{student_id}-")
    ]
    return max(candidates, key=len) if candidates else None


def _generate_image_embedding(image_paths: list[Path], ai_pipeline) -> tuple[np.ndarray, int, float]:
    import cv2

    vectors = []
    detection_scores = []
    for image_path in image_paths:
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            logger.warning("Skipping unreadable image %s", image_path)
            continue

        detections = ai_pipeline.detector.detect(image)
        face_data = ai_pipeline._select_best_face(detections, image.shape)
        if face_data is None or face_data.get("bbox") is None:
            logger.warning("Skipping image with no detectable face: %s", image_path)
            continue

        x1, y1, x2, y2 = face_data["bbox"]
        if x2 - x1 < 60 or y2 - y1 < 60:
            logger.warning("Skipping image with a face smaller than 60x60: %s", image_path)
            continue

        try:
            vector = np.asarray(
                ai_pipeline.recognizer.generate_embedding(image, face_data),
                dtype=np.float32,
            ).reshape(-1)
        except Exception as exc:
            logger.warning("Skipping image that failed embedding extraction (%s): %s", image_path, exc)
            continue

        norm = np.linalg.norm(vector)
        if vector.size == 0 or not np.isfinite(vector).all() or norm == 0:
            logger.warning("Skipping invalid embedding generated from %s", image_path)
            continue

        vectors.append(vector / norm)
        detection_scores.append(float(face_data.get("det_score", 0.0)))

    if not vectors:
        return np.array([], dtype=np.float32), 0, 0.0

    representative = calculate_representative_embedding(vectors).astype(np.float32)
    return representative, len(vectors), float(np.mean(detection_scores))


def _load_face_embeddings(directory: Path | None, students: dict[str, dict], now: datetime) -> dict[str, dict]:
    if directory is None:
        logger.info("Face embeddings skipped: no --face-embeddings-dir was supplied.")
        return {}
    if not directory.is_dir():
        raise FileNotFoundError(f"Face image directory not found: {directory}")

    from app.ai.pipeline import ai_pipeline
    from app.ai.detection.mock_detector import MockDetector
    from app.ai.recognition.mock_recognizer import MockRecognizer

    if (
        ai_pipeline.use_mock
        or isinstance(ai_pipeline.detector, MockDetector)
        or isinstance(ai_pipeline.recognizer, MockRecognizer)
    ):
        raise RuntimeError(
            "Image-based embeddings require real AI. Set USE_MOCK_AI=false and ensure the InsightFace models are available."
        )

    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    images_by_student: dict[str, list[Path]] = {}
    student_ids = set(students)
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in image_extensions:
            continue
        student_id = _student_id_for_image(path, directory, student_ids)
        if student_id is None:
            logger.warning("Ignoring image whose path does not identify a mock student: %s", path)
            continue
        images_by_student.setdefault(student_id, []).append(path)

    if not images_by_student:
        raise ValueError(
            "No face images matched the mock students. Use files like MOCK001_1.jpg "
            "or folders like <image-dir>/MOCK001/photo.jpg."
        )

    embeddings = {}
    for student_id, image_paths in images_by_student.items():
        vector, num_samples, quality = _generate_image_embedding(
            image_paths, ai_pipeline
        )
        if num_samples == 0:
            logger.warning("No usable face images found for student %s", student_id)
            continue
        timestamp = now.isoformat()
        embeddings[f"mock-{student_id}"] = {
            "student_id": student_id,
            "embedding": encode_embedding(vector),
            "num_samples": num_samples,
            "quality": quality,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        students[student_id]["face_enrolled"] = True

    logger.info("Generated %d face embeddings from %s", len(embeddings), directory)
    return embeddings


def seed_firestore(face_embeddings_dir: Path | None = None) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    documents = _mock_documents(now)
    documents["face_embeddings"] = _load_face_embeddings(
        face_embeddings_dir, documents["students"], now
    )

    db = get_db()
    counts = {}
    for collection_name, collection_documents in documents.items():
        for document_id, data in collection_documents.items():
            db.collection(collection_name).document(document_id).set(data, merge=True)
        counts[collection_name] = len(collection_documents)
    return counts


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed mock records into Firestore.")
    parser.add_argument(
        "--face-embeddings-dir",
        type=Path,
        default=os.environ.get("MOCK_FACE_EMBEDDINGS_DIR"),
        help="Folder containing student-ID-named face images or student-ID subfolders.",
    )
    parser.add_argument(
        "--allow-live",
        action="store_true",
        help="Explicitly allow writing mock data to a live Firebase project.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")
    if not emulator_host and not args.allow_live:
        raise SystemExit(
            "Refusing to seed live Firestore. Set FIRESTORE_EMULATOR_HOST or pass --allow-live explicitly."
        )
    if not emulator_host:
        logger.warning("--allow-live supplied: mock records will be written to live Firestore.")

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    init_firebase()
    try:
        counts = seed_firestore(args.face_embeddings_dir)
        logger.info("Mock seed complete (upserts per collection): %s", counts)
        logger.info("Mock admin login: mock.admin@example.test / %s", MOCK_ADMIN_PASSWORD)
        logger.info("Mock teacher login: taylor.morgan@example.test / %s", MOCK_TEACHER_PASSWORD)
        logger.info("Mock device: mock-rpi-01 / %s", MOCK_DEVICE_SECRET)
        logger.info("Student passwords follow MockStudent-<NNN>! (for example MOCK001).")
    finally:
        close_firebase()


if __name__ == "__main__":
    main()