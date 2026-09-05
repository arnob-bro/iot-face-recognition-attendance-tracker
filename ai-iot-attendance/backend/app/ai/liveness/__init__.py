"""Liveness detection package."""

from .base import LivenessChecker
from .mock_liveness import MockLiveness

try:
    from .mini_fasnet import MiniFASNet
except ImportError:  # pragma: no cover - optional runtime dependency
    MiniFASNet = None

__all__ = ["LivenessChecker", "MockLiveness", "MiniFASNet"]

