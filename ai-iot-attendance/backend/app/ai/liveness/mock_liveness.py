"""
Mock liveness checker for testing and development.

Always returns is_live=True so development can proceed
without the MiniFASNet ONNX models.
"""

import numpy as np
from typing import Any
from .base import LivenessChecker


class MockLiveness(LivenessChecker):
    """
    Mock liveness checker — always passes.
    Used when USE_MOCK_AI=true or when real models are unavailable.
    """

    def check(self, image: np.ndarray, face_data: dict[str, Any]) -> dict:
        return {
            "is_live": True,
            "score": 1.0
        }
