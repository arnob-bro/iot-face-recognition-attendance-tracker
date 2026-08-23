"""
Mock face recognizer for testing and development.
"""

import numpy as np
import hashlib
from typing import Any
from .base import RecognitionService


class MockRecognizer(RecognitionService):
    """
    Mock recognizer that returns a deterministic embedding based on image properties,
    or random if it can't distinguish.
    """

    def generate_embedding(self, face_image: np.ndarray, face_data: dict[str, Any] = None) -> np.ndarray:
        # Create a deterministic but somewhat distinct 512-dim array based on image mean
        # This helps in mock testing where the same image returns the same embedding
        if face_image is not None and face_image.size > 0:
            val = np.mean(face_image)
            # Use hash of the mean to seed a random generator
            seed = int(hashlib.md5(str(val).encode()).hexdigest(), 16) % (2**32)
            np.random.seed(seed)
        else:
            np.random.seed(42)

        embedding = np.random.randn(512).astype(np.float32)
        # L2 normalization
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding
