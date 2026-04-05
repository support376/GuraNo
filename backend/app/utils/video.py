"""Video utility functions."""
import cv2
import numpy as np


def decode_jpeg(data: bytes) -> np.ndarray | None:
    """Decode JPEG bytes to OpenCV frame."""
    arr = np.frombuffer(data, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return frame


def encode_jpeg(frame: np.ndarray, quality: int = 80) -> bytes:
    """Encode OpenCV frame to JPEG bytes."""
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes()


def resize_frame(frame: np.ndarray, max_width: int = 640) -> np.ndarray:
    """Resize frame maintaining aspect ratio."""
    h, w = frame.shape[:2]
    if w <= max_width:
        return frame
    ratio = max_width / w
    new_size = (max_width, int(h * ratio))
    return cv2.resize(frame, new_size)
