import cv2
import numpy as np


def draw_overlay(frame: np.ndarray, status: str, student_name: str = "", confidence: float = 0.0) -> np.ndarray:
    """Draw a semi-transparent overlay bar at the bottom of the frame."""
    overlay = frame.copy()
    h, w = frame.shape[:2]
    bar_h = 72
    y0 = max(0, h - bar_h)

    colors = {
        "idle": (80, 80, 80),
        "matched": (0, 200, 80),
        "unknown": (0, 165, 255),
        "duplicate": (0, 120, 255),
        "no_face": (50, 50, 50),
    }
    color = colors.get(status, (80, 80, 80))

    cv2.rectangle(overlay, (0, y0), (w, h), color, -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

    label = status.upper()
    text = student_name or label
    if status == "matched" and confidence > 0:
        text = f"{student_name} ({confidence:.2%})"
    elif status == "unknown" and confidence > 0:
        text = f"Unknown ({confidence:.2%})"

    cv2.putText(
        frame,
        text,
        (20, h - 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return frame
