"""Eye tracking: blink detection and gaze direction."""
import logging
from collections import deque

import numpy as np

logger = logging.getLogger(__name__)

# Blink detection thresholds
EAR_BLINK_THRESHOLD = 0.2
BLINK_CONSECUTIVE_FRAMES = 2


class EyeTracker:
    def __init__(self):
        self.ear_history: deque[float] = deque(maxlen=90)  # 3 sec at 30fps
        self.blink_count = 0
        self.blink_timestamps: list[float] = []
        self._consecutive_low = 0
        self._in_blink = False

    def process_frame(self, metrics: dict, timestamp: float):
        """Process eye metrics from a frame."""
        ear = metrics.get("ear_mean", 0.5)
        self.ear_history.append(ear)

        # Blink detection
        if ear < EAR_BLINK_THRESHOLD:
            self._consecutive_low += 1
        else:
            if self._consecutive_low >= BLINK_CONSECUTIVE_FRAMES and self._in_blink:
                self.blink_count += 1
                self.blink_timestamps.append(timestamp)
                self._in_blink = False
            elif self._consecutive_low >= BLINK_CONSECUTIVE_FRAMES:
                self._in_blink = True
            self._consecutive_low = 0

    def get_blink_rate(self, window_sec: float = 10.0) -> float:
        """Get blink rate per minute over the last window."""
        if not self.blink_timestamps:
            return 0.0

        now = self.blink_timestamps[-1]
        recent = [t for t in self.blink_timestamps if now - t <= window_sec]
        if window_sec > 0:
            return len(recent) * (60.0 / window_sec)
        return 0.0

    def get_gaze_stability(self) -> float:
        """
        Get gaze stability score (0 = very unstable, 1 = stable).
        Based on EAR variance as proxy.
        """
        if len(self.ear_history) < 10:
            return 1.0
        variance = float(np.var(list(self.ear_history)))
        # Higher variance = less stable
        stability = max(0.0, 1.0 - variance * 100)
        return stability
