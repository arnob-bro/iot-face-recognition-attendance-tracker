"""
Abstract base class for liveness detection (anti-spoofing).
"""

from abc import ABC, abstractmethod
from typing import Any
import numpy as np


class LivenessChecker(ABC):
    """
    Interface for face liveness detection models.
    """

    @abstractmethod
    def check(self, image: np.ndarray, face_data: dict[str, Any]) -> dict:
        """
        Check whether a detected face is a real, live person
        or a spoof (photo, screen, mask).

        Args:
            image: Full BGR numpy array of the original frame.
            face_data: Detection result dict containing at minimum:
                - "bbox": [x1, y1, x2, y2]

        Returns:
            Dictionary with:
            - "is_live": bool
            - "score": float (0.0 = definitely fake, 1.0 = definitely real)
        """
        pass
