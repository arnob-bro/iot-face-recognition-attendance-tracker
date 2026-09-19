import logging
import threading
import time
from datetime import datetime, timezone

import cv2
import numpy as np

from api.client import AttendanceAPIClient, NetworkError
from camera.capture import WebcamCapture
from config import settings
from hardware.esp32_bridge import ESP32Bridge
from offline.queue import OfflineQueue
from ui.display import draw_overlay

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class RecognitionWorker:
    """Run network and attendance work away from the camera display loop."""

    def __init__(self, api_client, queue, bridge, settings):
        self.api_client = api_client
        self.queue = queue
        self.bridge = bridge
        self.settings = settings
        self._condition = threading.Condition()
        self._latest_frame: np.ndarray | None = None
        self._active_session_id: str | None = None
        self._result = ("idle", "", 0.0)
        self._last_recorded: dict = {}
        self._last_session_poll = 0.0
        self._last_queue_drain = 0.0
        self._stop = False
        self._thread = threading.Thread(target=self._run, name="recognition-worker", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def submit(self, frame: np.ndarray) -> None:
        with self._condition:
            self._latest_frame = frame.copy()
            self._condition.notify()

    def get_result(self) -> tuple[str, str, float]:
        with self._condition:
            return self._result

    def stop(self) -> None:
        with self._condition:
            self._stop = True
            self._condition.notify()
        self._thread.join(timeout=2.0)

    def _run(self) -> None:
        while True:
            with self._condition:
                while self._latest_frame is None and not self._stop:
                    self._condition.wait(timeout=0.5)
                if self._stop:
                    return
                frame = self._latest_frame
                self._latest_frame = None

            self._poll_background_tasks()
            if frame is not None:
                self._recognize(frame)

    def _poll_background_tasks(self) -> None:
        now = time.time()
        if now - self._last_session_poll >= 30:
            try:
                active_session = self.api_client.get_active_session()
                with self._condition:
                    self._active_session_id = active_session.get("session_id") if active_session else None
                self._last_session_poll = now
            except NetworkError as exc:
                logger.warning(f"Session poll failed: {exc}")

        if now - self._last_queue_drain >= 300:
            try:
                self.queue.drain(self.api_client)
                self._last_queue_drain = now
            except NetworkError:
                logger.warning("Offline queue drain failed; will retry later.")

    def _recognize(self, frame: np.ndarray) -> None:
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
        ok, encoded = cv2.imencode(".jpg", frame, encode_param)
        if not ok:
            return

        try:
            recognition = self.api_client.recognize_face(encoded.tobytes())
        except NetworkError as exc:
            logger.warning(f"Recognition request failed: {exc}")
            return

        status = "idle"
        student_name = ""
        confidence = 0.0

        if recognition.get("matched"):
            status = "matched"
            student_name = str(recognition.get("student_id", "Unknown"))
            confidence = float(recognition.get("confidence", 0.0))
            self._record_attendance(student_name, confidence)
        elif recognition.get("matched") is False:
            status = "unknown"
            confidence = float(recognition.get("confidence", 0.0))

        with self._condition:
            self._result = (status, student_name, confidence)

    def _record_attendance(self, student_id: str, confidence: float) -> None:
        with self._condition:
            active_session_id = self._active_session_id
        if not active_session_id:
            return

        now = datetime.now(timezone.utc).isoformat()
        last_time = self._last_recorded.get("timestamp", 0)
        now_ts = time.time()
        if self._last_recorded.get("student_id") == student_id and now_ts - last_time < self.settings.attendance_cooldown_seconds:
            return

        try:
            self.api_client.record_attendance(active_session_id, student_id, confidence, "face_recognition")
            self._last_recorded = {"student_id": student_id, "timestamp": now_ts}
            logger.info(f"Recorded attendance for {student_id} (confidence={confidence:.2f})")
            self.bridge.open_door()
            self.bridge.buzz()
            self.bridge.led_green()
        except NetworkError as exc:
            if exc.retryable:
                logger.warning("Attendance record failed; saved to offline queue.")
                self.queue.enqueue(active_session_id, student_id, now, confidence)
            else:
                logger.warning(f"Attendance record rejected: {exc}")


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
        api_client.login_device(settings.device_id, settings.device_secret)
        logger.info("Authenticated to backend API.")

        worker = RecognitionWorker(api_client, queue, bridge, settings)
        worker.start()
        frame_id = 0
        skip_n = max(1, settings.recognize_every_n_frames)
        logger.info(f"Background recognition enabled: every {skip_n} frame(s).")

        while True:
            frame = capture.read_frame()
            if frame is None:
                time.sleep(0.1)
                continue

            if frame_id % skip_n == 0:
                worker.submit(frame)

            last_status, last_student_name, last_confidence = worker.get_result()
            frame = draw_overlay(frame, last_status, last_student_name, last_confidence)
            cv2.imshow("AI Attendance Camera", frame)
            frame_id += 1

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user.")
    finally:
        if "worker" in locals():
            worker.stop()
        capture.release()
        bridge.close()
        queue.close()
        api_client.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

