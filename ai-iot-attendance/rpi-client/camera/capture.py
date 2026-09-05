import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class WebcamCapture:
    """Simple webcam wrapper with automatic reconnects."""

    def __init__(self, index: int = 0, width: int = 640, height: int = 480, fps: int = 15):
        self.index = index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None
        self.consecutive_failures = 0
        self._open()

    def _open(self) -> bool:
        self.cap = cv2.VideoCapture(self.index)
        if not self.cap.isOpened():
            logger.warning(f"Failed to open camera index {self.index}.")
            self.cap = None
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        logger.info(f"Camera {self.index} opened successfully.")
        return True

    def _reconnect(self) -> None:
        if self.cap is not None:
            self.cap.release()
        self.cap = None
        self.consecutive_failures = 0
        if self._open():
            logger.info("Camera reconnected successfully.")
        else:
            logger.warning("Camera reconnect failed.")

    def read_frame(self) -> Optional[np.ndarray]:
        if self.cap is None:
            if not self._open():
                return None

        ok, frame = self.cap.read()
        if not ok or frame is None:
            self.consecutive_failures += 1
            logger.warning(f"Camera read failed ({self.consecutive_failures}/5).")
            if self.consecutive_failures >= 5:
                self._reconnect()
            return None

        self.consecutive_failures = 0
        return frame

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None
