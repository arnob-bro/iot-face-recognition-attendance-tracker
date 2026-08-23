"""
Mock face detector for testing and development on machines without GPU/models.
"""

import numpy as np
from typing import Any
from .base import FaceDetector


class MockDetector(FaceDetector):
    """
    Mock detector that always returns a single centered bounding box
    if the image is valid.
    """

    def detect(self, image: np.ndarray) -> list[dict[str, Any]]:
        if image is None or image.size == 0:
            return []

        h, w = image.shape[:2]
        
        # Create a centered bounding box taking up 50% of the image
        x1 = int(w * 0.25)
        y1 = int(h * 0.25)
        x2 = int(w * 0.75)
        y2 = int(h * 0.75)

        # Mock 5-point landmarks
        landmarks = np.array([
            [x1 + (x2 - x1) * 0.3, y1 + (y2 - y1) * 0.3], # Left eye
            [x1 + (x2 - x1) * 0.7, y1 + (y2 - y1) * 0.3], # Right eye
            [x1 + (x2 - x1) * 0.5, y1 + (y2 - y1) * 0.5], # Nose
            [x1 + (x2 - x1) * 0.3, y1 + (y2 - y1) * 0.7], # Left mouth
            [x1 + (x2 - x1) * 0.7, y1 + (y2 - y1) * 0.7], # Right mouth
        ])

        return [{
            "bbox": [x1, y1, x2, y2],
            "det_score": 0.99,
            "landmark_5": landmarks
        }]
