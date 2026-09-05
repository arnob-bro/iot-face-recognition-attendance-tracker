import logging
import time
from datetime import datetime, timezone

import cv2

from api.client import AttendanceAPIClient, NetworkError
from camera.capture import WebcamCapture
from config import settings
from hardware.esp32_bridge import ESP32Bridge
from offline.queue import OfflineQueue
from ui.display import draw_overlay

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting Raspberry Pi attendance client.")

    api_client = AttendanceAPIClient(settings.api_url)
    queue = OfflineQueue()
    bridge = ESP32Bridge(settings.esp32_serial_port, settings.esp32_baud_rate)
    capture = WebcamCapture(
        index=settings.camera_index,
        width=settings.camera_width,
        height=settings.camera_height,
        fps=settings.camera_fps,
    )

    try:
        api_client.login(settings.rpi_email, settings.rpi_password)
        logger.info("Authenticated to backend API.")

        last_session_poll = 0.0
        last_queue_drain = 0.0
        last_recorded = {}
        frame_id = 0

        while True:
            frame = capture.read_frame()
            if frame is None:
                draw_overlay(frame if frame is not None else None, "no_face")
                time.sleep(0.1)
                continue

            if time.time() - last_session_poll >= 30:
                try:
                    active_session = api_client.get_active_session(settings.course_id)
                    if active_session:
                        logger.info(f"Active session detected: {active_session.get('session_id')}")
                        last_session_poll = time.time()
                    else:
                        logger.info("No active session found; waiting for a class to start.")
                        last_session_poll = time.time()
                except NetworkError as exc:
                    logger.warning(f"Session poll failed: {exc}")

            if time.time() - last_queue_drain >= 300:
                try:
                    queue.drain(api_client, settings.course_id)
                    last_queue_drain = time.time()
                except NetworkError:
                    logger.warning("Offline queue drain failed; will retry later.")

            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
            _, encoded = cv2.imencode(".jpg", frame, encode_param)
            jpeg_bytes = encoded.tobytes()

            try:
                recognition = api_client.recognize_face(jpeg_bytes)
            except NetworkError as exc:
                logger.warning(f"Recognition request failed; queueing offline fallback: {exc}")
                if settings.course_id:
                    queue.enqueue(settings.course_id, "offline_unknown", datetime.now(timezone.utc).isoformat(), 0.0)
                continue

            status = "idle"
            student_name = ""
            confidence = 0.0

            if recognition.get("matched"):
                status = "matched"
                student_name = str(recognition.get("student_id", "Unknown"))
                confidence = float(recognition.get("confidence", 0.0))
                session_id = None
                try:
                    active_session = api_client.get_active_session(settings.course_id)
                    if active_session:
                        session_id = active_session.get("session_id")
                except NetworkError:
                    session_id = None

                if session_id:
                    now = datetime.now(timezone.utc).isoformat()
                    student_key = str(recognition.get("student_id"))
                    last_key = last_recorded.get("student_id")
                    last_time = last_recorded.get("timestamp", 0)
                    now_ts = time.time()
                    if not last_key or last_key != student_key or (now_ts - last_time) >= settings.attendance_cooldown_seconds:
                        try:
                            api_client.record_attendance(session_id, student_key, confidence, "face_recognition")
                            queue.enqueue(session_id, student_key, now, confidence)
                            last_recorded = {"student_id": student_key, "timestamp": now_ts}
                            logger.info(f"Recorded attendance for {student_key} (confidence={confidence:.2f})")
                            bridge.open_door()
                            bridge.buzz()
                            bridge.led_green()
                        except NetworkError:
                            logger.warning("Attendance record failed; saved to offline queue.")
                            queue.enqueue(session_id, student_key, now, confidence)
                else:
                    status = "unknown"
            elif recognition.get("matched") is False:
                status = "unknown"
                confidence = float(recognition.get("confidence", 0.0))

            frame = draw_overlay(frame, status, student_name, confidence)
            cv2.imshow("AI Attendance Camera", frame)
            frame_id += 1

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user.")
    finally:
        capture.release()
        bridge.close()
        queue.close()
        api_client.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
