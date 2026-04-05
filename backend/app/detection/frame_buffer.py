"""Rolling frame buffer for capturing video around lie detection events."""
from collections import deque
from dataclasses import dataclass


@dataclass
class BufferedFrame:
    data: bytes
    timestamp: float


class FrameBuffer:
    def __init__(self, max_frames: int = 300):
        self.frames: deque[BufferedFrame] = deque(maxlen=max_frames)

    def add(self, data: bytes, timestamp: float):
        self.frames.append(BufferedFrame(data=data, timestamp=timestamp))

    def get_window(self, center_ts: float, window_sec: float = 2.0) -> list[BufferedFrame]:
        """Get frames within a time window around a timestamp."""
        return [
            f for f in self.frames
            if abs(f.timestamp - center_ts) <= window_sec
        ]

    def get_latest(self) -> BufferedFrame | None:
        return self.frames[-1] if self.frames else None
