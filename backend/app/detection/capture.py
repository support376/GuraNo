"""Screen capture and video clip extraction on lie detection."""
import logging
import os
from datetime import datetime

import cv2
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


def save_screenshot(frame_data: bytes, session_id: str, timestamp: float) -> str:
    """Save a screenshot when a lie is detected. Returns the file path."""
    frame_array = np.frombuffer(frame_data, dtype=np.uint8)
    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

    if frame is None:
        return ""

    dt = datetime.fromtimestamp(timestamp)
    filename = f"lie_{session_id}_{dt.strftime('%H%M%S')}.jpg"
    filepath = os.path.join(settings.capture_dir, filename)

    os.makedirs(settings.capture_dir, exist_ok=True)
    cv2.imwrite(filepath, frame)
    logger.info(f"Screenshot saved: {filepath}")

    return f"/captures/{filename}"


def save_clip(frames: list, session_id: str, timestamp: float, fps: float = 10.0) -> str:
    """Save a short video clip around the lie detection moment."""
    if not frames:
        return ""

    dt = datetime.fromtimestamp(timestamp)
    filename = f"clip_{session_id}_{dt.strftime('%H%M%S')}.mp4"
    filepath = os.path.join(settings.capture_dir, filename)
    os.makedirs(settings.capture_dir, exist_ok=True)

    # Decode first frame to get dimensions
    first_data = frames[0][0] if isinstance(frames[0], tuple) else frames[0]
    first_array = np.frombuffer(first_data, dtype=np.uint8)
    first_frame = cv2.imdecode(first_array, cv2.IMREAD_COLOR)
    if first_frame is None:
        return ""

    h, w = first_frame.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(filepath, fourcc, fps, (w, h))

    for item in frames:
        data = item[0] if isinstance(item, tuple) else item
        arr = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is not None:
            writer.write(frame)

    writer.release()
    logger.info(f"Clip saved: {filepath}")
    return f"/captures/{filename}"
