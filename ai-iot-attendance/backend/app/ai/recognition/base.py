"""
Abstract base class for face recognition models.
"""

from abc import ABC, abstractmethod
from typing import Any
import numpy as np


class RecognitionService(ABC):
    """
    Interface for face recognition models.
    """

    @abstractmethod
    def generate_embedding(self, face_image: np.ndarray, face_data: dict[str, Any] = None) -> np.ndarray:
        """
        Generate a face embedding vector from a cropped/aligned face image.

        Args:
            face_image: numpy array of the face image (BGR).
            face_data: Optional pre-computed data from detection (like landmarks).

        Returns:
            numpy array representing the 512-dimensional face embedding.
        """
        pass
