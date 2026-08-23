"""
Real face recognizer using InsightFace's ArcFace model.
"""

import logging
from typing import Any
import numpy as np

try:
    from insightface.app import FaceAnalysis
except ImportError:
    FaceAnalysis = None

from .base import RecognitionService

logger = logging.getLogger(__name__)


class ArcFaceRecognizer(RecognitionService):
    """
    Face recognizer using ArcFace from the InsightFace library.
    """

    def __init__(self, root_dir: str = "./models"):
        if FaceAnalysis is None:
            raise ImportError("insightface is not installed. Please install it to use ArcFaceRecognizer.")
        
        # Initialize FaceAnalysis. Note: insightface asserts 'detection' must be present
        self.app = FaceAnalysis(
            name="buffalo_l",
            root=root_dir,
            allowed_modules=["detection", "recognition"]
        )
        
        # Prepare the model (CPU mode for consistency with detector)
        self.app.prepare(ctx_id=-1, det_size=(640, 640))
        logger.info("ArcFace recognizer initialized successfully.")

    def generate_embedding(self, face_image: np.ndarray, face_data: dict[str, Any] = None) -> np.ndarray:
        if face_image is None or face_image.size == 0:
            raise ValueError("Invalid face image provided for embedding generation.")

        # If the detector passed the raw InsightFace object, we can use it directly
        # to extract the embedding. InsightFace recognizer needs the face object
        # with bounding boxes and landmarks to align the face before embedding.
        
        raw_face = face_data.get("_raw_face") if face_data else None
        
        if raw_face is not None:
            # The recognition model expects the image and the face object
            # It modifies the face object in place to add the 'embedding' attribute
            self.app.models["recognition"].get(face_image, raw_face)
            
            if raw_face.embedding is not None:
                # Normalize the embedding (L2 normalization is standard for ArcFace)
                emb = raw_face.embedding
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = emb / norm
                return emb
                
        raise ValueError("Could not generate embedding. Missing raw face data with landmarks.")
