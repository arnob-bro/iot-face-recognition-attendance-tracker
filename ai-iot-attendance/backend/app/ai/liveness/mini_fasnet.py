"""
Real liveness detection using MiniFASNet ONNX models.

Uses two MiniFASNet variants (V1SE and V2) for anti-spoofing.
Models are automatically downloaded on first use from the
Silent-Face-Anti-Spoofing project.

References:
  https://github.com/minivision-ai/Silent-Face-Anti-Spoofing
"""

import logging
import os
import urllib.request
from pathlib import Path
from typing import Any

import cv2
import numpy as np

try:
    import onnxruntime as ort
except ImportError:
    ort = None

from .base import LivenessChecker

logger = logging.getLogger(__name__)

# --- Model download configuration ---
# These are the two MiniFASNet ONNX model files.
# The download URLs point to community-hosted ONNX conversions of the
# Silent-Face-Anti-Spoofing models. If the URLs become stale, place the
# .onnx files manually into backend/models/ and the download step is skipped.
MODEL_FILES = {
    "MiniFASNetV2.onnx": {
        "input_size": (80, 80),
        "urls": [
            "https://github.com/Ashi-Jain23/Silent-Face-Anti-Spoofing-onnx/raw/main/resources/anti_spoof_models/2.7_80x80_MiniFASNetV2.onnx",
            "https://raw.githubusercontent.com/minivision-ai/Silent-Face-Anti-Spoofing/master/resources/anti_spoof_models/2.7_80x80_MiniFASNetV2.onnx",
        ],
    },
    "MiniFASNetV1SE.onnx": {
        "input_size": (80, 80),
        "urls": [
            "https://github.com/Ashi-Jain23/Silent-Face-Anti-Spoofing-onnx/raw/main/resources/anti_spoof_models/4_0_0_80x80_MiniFASNetV1SE.onnx",
            "https://raw.githubusercontent.com/minivision-ai/Silent-Face-Anti-Spoofing/master/resources/anti_spoof_models/4_0_0_80x80_MiniFASNetV1SE.onnx",
        ],
    },
}

# Liveness threshold — if the fused "real" probability is above this, the face is live.
LIVENESS_THRESHOLD = 0.5


def _download_model(dest_path: str, urls: list[str]) -> bool:
    """
    Attempt to download a model file from a list of fallback URLs.
    Returns True if download succeeded, False otherwise.
    """
    for url in urls:
        try:
            logger.info(f"Downloading liveness model from {url} ...")
            urllib.request.urlretrieve(url, dest_path)
            file_size = os.path.getsize(dest_path)
            if file_size > 10_000:  # Sanity check — models should be > 10 KB
                logger.info(f"Downloaded successfully ({file_size:,} bytes): {dest_path}")
                return True
            else:
                logger.warning(f"Downloaded file is suspiciously small ({file_size} bytes), trying next URL...")
                os.remove(dest_path)
        except Exception as e:
            logger.warning(f"Failed to download from {url}: {e}")
            if os.path.exists(dest_path):
                os.remove(dest_path)
    return False


def _ensure_models(model_dir: str) -> dict[str, str]:
    """
    Check that all required ONNX models exist in model_dir.
    If any are missing, attempt to download them.
    Returns a dict of {model_name: full_path} for models that are available.
    """
    os.makedirs(model_dir, exist_ok=True)
    available = {}

    for model_name, info in MODEL_FILES.items():
        model_path = os.path.join(model_dir, model_name)

        if os.path.isfile(model_path):
            available[model_name] = model_path
            continue

        # Try downloading
        if _download_model(model_path, info["urls"]):
            available[model_name] = model_path
        else:
            logger.error(
                f"Could not download liveness model '{model_name}'. "
                f"Please download it manually from "
                f"https://github.com/minivision-ai/Silent-Face-Anti-Spoofing "
                f"and place the ONNX file in: {model_dir}/"
            )

    return available


def _crop_face(image: np.ndarray, bbox: list, scale: float = 2.7) -> np.ndarray:
    """
    Crop and pad a face region from the full image, expanding
    the bounding box by `scale` factor to include context
    (forehead, chin, etc.) that helps liveness detection.
    """
    h, w = image.shape[:2]
    x1, y1, x2, y2 = [int(v) for v in bbox]

    face_w = x2 - x1
    face_h = y2 - y1
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2

    # Expand to square using the larger dimension, scaled up
    side = int(max(face_w, face_h) * scale)
    half = side // 2

    # Calculate crop coordinates (may go out of bounds)
    crop_x1 = cx - half
    crop_y1 = cy - half
    crop_x2 = cx + half
    crop_y2 = cy + half

    # Calculate padding needed if crop goes out of image bounds
    pad_left = max(0, -crop_x1)
    pad_top = max(0, -crop_y1)
    pad_right = max(0, crop_x2 - w)
    pad_bottom = max(0, crop_y2 - h)

    # Clamp to image bounds
    crop_x1 = max(0, crop_x1)
    crop_y1 = max(0, crop_y1)
    crop_x2 = min(w, crop_x2)
    crop_y2 = min(h, crop_y2)

    crop = image[crop_y1:crop_y2, crop_x1:crop_x2]

    # Pad if needed (replicate border)
    if pad_left > 0 or pad_top > 0 or pad_right > 0 or pad_bottom > 0:
        crop = cv2.copyMakeBorder(
            crop, pad_top, pad_bottom, pad_left, pad_right,
            cv2.BORDER_REPLICATE
        )

    return crop


class MiniFASNet(LivenessChecker):
    """
    Real liveness detector using MiniFASNet V1SE + V2 ONNX models.

    Runs both models on the face crop and fuses their outputs
    (averaged softmax probabilities) to determine liveness.
    """

    def __init__(self, root_dir: str = "./models"):
        if ort is None:
            raise ImportError(
                "onnxruntime is not installed. "
                "Please install it: pip install onnxruntime"
            )

        # Download models if needed
        available = _ensure_models(root_dir)

        if not available:
            raise FileNotFoundError(
                "No liveness models found or downloaded. "
                "Cannot initialize MiniFASNet liveness checker."
            )

        # Load available ONNX sessions
        self.sessions: list[tuple[str, ort.InferenceSession, tuple[int, int]]] = []

        sess_options = ort.SessionOptions()
        sess_options.inter_op_num_threads = 1
        sess_options.intra_op_num_threads = 1

        for model_name, model_path in available.items():
            try:
                session = ort.InferenceSession(
                    model_path,
                    sess_options,
                    providers=["CPUExecutionProvider"]
                )
                input_size = MODEL_FILES[model_name]["input_size"]
                self.sessions.append((model_name, session, input_size))
                logger.info(f"Loaded liveness model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load liveness model {model_name}: {e}")

        if not self.sessions:
            raise RuntimeError("All liveness model sessions failed to load.")

        logger.info(
            f"MiniFASNet liveness checker initialized with "
            f"{len(self.sessions)} model(s)."
        )

    def _preprocess(self, face_crop: np.ndarray, target_size: tuple[int, int]) -> np.ndarray:
        """
        Preprocess a face crop for ONNX inference.
        Resize, normalize, and transpose to NCHW format.
        """
        # Resize to model input size
        resized = cv2.resize(face_crop, target_size, interpolation=cv2.INTER_LINEAR)

        # Convert BGR to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        # Normalize to [0, 1] then apply ImageNet-style normalization
        img = rgb.astype(np.float32) / 255.0
        mean = np.array([0.5, 0.5, 0.5], dtype=np.float32)
        std = np.array([0.5, 0.5, 0.5], dtype=np.float32)
        img = (img - mean) / std

        # Transpose from HWC to CHW and add batch dimension -> (1, 3, H, W)
        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, axis=0)

        return img

    def _softmax(self, logits: np.ndarray) -> np.ndarray:
        """Apply softmax to logits."""
        exp = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
        return exp / np.sum(exp, axis=-1, keepdims=True)

    def check(self, image: np.ndarray, face_data: dict[str, Any]) -> dict:
        bbox = face_data.get("bbox")
        if bbox is None:
            return {"is_live": False, "score": 0.0}

        # Crop the face region with context padding
        face_crop = _crop_face(image, bbox, scale=2.7)

        if face_crop.size == 0:
            return {"is_live": False, "score": 0.0}

        # Run each model and collect "real" probabilities
        real_scores = []

        for model_name, session, input_size in self.sessions:
            try:
                input_tensor = self._preprocess(face_crop, input_size)
                input_name = session.get_inputs()[0].name
                outputs = session.run(None, {input_name: input_tensor})
                logits = outputs[0]  # shape: (1, 2) or (1, 3)

                probs = self._softmax(logits[0])

                # Convention: class 0 = fake, class 1 = real
                # (Some models use 3 classes; last class is "real")
                real_prob = float(probs[-1])
                real_scores.append(real_prob)

            except Exception as e:
                logger.error(f"Liveness inference error ({model_name}): {e}")
                continue

        if not real_scores:
            # All models failed — fail-safe: reject
            return {"is_live": False, "score": 0.0}

        # Fuse scores by averaging
        fused_score = sum(real_scores) / len(real_scores)
        is_live = fused_score >= LIVENESS_THRESHOLD

        return {
            "is_live": is_live,
            "score": round(fused_score, 4)
        }
