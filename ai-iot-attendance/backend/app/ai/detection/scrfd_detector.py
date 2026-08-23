"""
Real face detector using InsightFace's SCRFD model.
"""

import logging
from typing import Any
import numpy as np

try:
    from insightface.app import FaceAnalysis
except ImportError:
    FaceAnalysis = None

from .base import FaceDetector

logger = logging.getLogger(__name__)


class SCRFDDetector(FaceDetector):
    """
    Face detector using SCRFD from the InsightFace library.
    """

    def __init__(self, root_dir: str = "./models"):
        if FaceAnalysis is None:
            raise ImportError("insightface is not installed. Please install it to use SCRFDDetector.")
        
        # Initialize FaceAnalysis with only the detection module to save memory
        self.app = FaceAnalysis(
            name="buffalo_l",
            root=root_dir,
            allowed_modules=["detection"]
        )
        
        # Prepare the model (use ctx_id=0 for GPU, -1 for CPU)
        # For edge devices / Raspberry Pi, CPU is typically used
        self.app.prepare(ctx_id=-1, det_size=(640, 640))
        logger.info("SCRFD face detector initialized successfully.")

    def detect(self, image: np.ndarray) -> list[dict[str, Any]]:
        if image is None or image.size == 0:
            return []

        # InsightFace expects BGR format (OpenCV default)
        faces = self.app.get(image)
        
        results = []
        for face in faces:
            results.append({
                "bbox": face.bbox.tolist() if face.bbox is not None else None,
                "det_score": float(face.det_score) if face.det_score is not None else 0.0,
                "landmark_5": face.kps if face.kps is not None else None,
                # Store the raw Face object internally if needed by recognizer
                "_raw_face": face 
            })
            
        return results
