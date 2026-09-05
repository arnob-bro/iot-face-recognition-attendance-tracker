"""
AI Pipeline Orchestrator.

Combines Detection, Liveness, and Recognition into a single workflow.
Uses Mock adapters if configured in environment variables.
"""

import logging
import numpy as np

from app.core.config import settings

# Interfaces
from .detection.base import FaceDetector
from .recognition.base import RecognitionService
from .liveness.base import LivenessChecker

# Implementations
from .detection.mock_detector import MockDetector
from .recognition.mock_recognizer import MockRecognizer
from .liveness.mock_liveness import MockLiveness

try:
    from .detection.scrfd_detector import SCRFDDetector
    from .recognition.arcface_recognizer import ArcFaceRecognizer
    from .liveness.mini_fasnet import MiniFASNet
except ImportError:
    SCRFDDetector = None
    ArcFaceRecognizer = None
    MiniFASNet = None

logger = logging.getLogger(__name__)


class AIPipeline:
    """
    Main orchestration class for the AI workflow.
    """

    def __init__(self):
        self.use_mock = settings.use_mock_ai
        self.liveness_checker: LivenessChecker | None = None

        logger.info(f"Initializing AI Pipeline (Mock Mode: {self.use_mock})")

        if self.use_mock or SCRFDDetector is None or ArcFaceRecognizer is None:
            if not self.use_mock:
                logger.warning("Real AI modules not available (insightface missing?). Falling back to Mock AI.")
            self.detector: FaceDetector = MockDetector()
            self.recognizer: RecognitionService = MockRecognizer()
        else:
            self.detector = SCRFDDetector(root_dir=settings.model_dir)
            self.recognizer = ArcFaceRecognizer(root_dir=settings.model_dir)

        if settings.liveness_enabled:
            if self.use_mock or MiniFASNet is None:
                logger.info("Using mock liveness checker.")
                self.liveness_checker = MockLiveness()
            else:
                try:
                    self.liveness_checker = MiniFASNet(root_dir=settings.model_dir)
                    logger.info("Liveness checker initialized: MiniFASNet")
                except Exception as exc:
                    logger.warning(f"Failed to initialize MiniFASNet, falling back to mock liveness: {exc}")
                    self.liveness_checker = MockLiveness()

    def process_frame(self, image: np.ndarray) -> dict:
        """
        Process a single image frame for face detection and recognition.
        
        Args:
            image: BGR numpy array
            
        Returns:
            Dictionary with results:
            - success: bool
            - message: str
            - face_data: dict (bbox, landmarks)
            - embedding: np.ndarray (if successful)
            - liveness: dict (if checked)
        """
        # 1. Detection
        detections = self.detector.detect(image)
        
        if not detections:
            return {"success": False, "message": "No face detected in frame."}
            
        if len(detections) > 1:
            # For strict enrollment/recognition, we often want exactly one face
            return {"success": False, "message": "Multiple faces detected. Please ensure only one face is in frame."}
            
        face_data = detections[0]
        
        # Check basic quality / size
        bbox = face_data.get("bbox")
        if bbox:
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            if w < 60 or h < 60:
                return {"success": False, "message": "Face is too small. Move closer to the camera."}
                
        # 2. Liveness check
        liveness_score = 1.0
        if settings.liveness_enabled and self.liveness_checker is not None:
            try:
                liveness_result = self.liveness_checker.check(image, face_data)
                liveness_score = float(liveness_result.get("score", 0.0))
                if not liveness_result.get("is_live", False):
                    return {
                        "success": False,
                        "message": "Liveness check failed. Please don't use a photo.",
                        "face_data": face_data,
                        "liveness_score": liveness_score,
                    }
            except Exception as exc:
                logger.warning(f"Liveness check failed: {exc}")
                return {
                    "success": False,
                    "message": "Liveness check failed. Please don't use a photo.",
                    "face_data": face_data,
                    "liveness_score": 0.0,
                }

        # 3. Recognition (Generate Embedding)
        try:
            embedding = self.recognizer.generate_embedding(image, face_data)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return {"success": False, "message": f"Failed to generate embedding: {e}"}

        return {
            "success": True,
            "message": "Face processed successfully.",
            "face_data": face_data,
            "embedding": embedding,
            "liveness_score": liveness_score,
        }

# Global singleton instance
ai_pipeline = AIPipeline()
