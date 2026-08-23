"""
Abstract base class for face detectors.
"""

from abc import ABC, abstractmethod
from typing import Any
import numpy as np


class FaceDetector(ABC):
    """
    Interface for face detection models.
    """

    @abstractmethod
    def detect(self, image: np.ndarray) -> list[dict[str, Any]]:
        """
        Detect faces in a given image (BGR format).

        Args:
            image: numpy array representing the image (H, W, C) in BGR format.

        Returns:
            A list of dictionaries containing face detection results.
            Expected keys in each dict:
            - "bbox": [x1, y1, x2, y2]
            - "det_score": float (confidence)
            - "landmark_5": numpy array (5, 2) of landmarks (optional)
        """
        pass
