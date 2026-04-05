"""Micro-expression detection from temporal AU analysis."""
import logging
from collections import deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Micro-expression duration: 40-200ms
# At 30fps: 1-6 frames
MIN_FRAMES = 1
MAX_FRAMES = 6


@dataclass
class MicroExpression:
    au_id: str
    start_frame: int
    end_frame: int
    duration_ms: float
    peak_intensity: float
    expression_type: str  # surprise, fear, disgust, sadness, etc.


# AU to emotion mapping
AU_EMOTION_MAP = {
    "AU1+AU2": "놀람 (surprise)",
    "AU4": "인지 부하 (cognitive load)",
    "AU9": "역겨움 (disgust)",
    "AU15": "슬픔 (sadness)",
}


class MicroExpressionDetector:
    def __init__(self, fps: float = 30.0):
        self.fps = fps
        self.frame_duration_ms = 1000.0 / fps
        # History of AU intensities per frame
        self.au_history: deque[dict[str, float]] = deque(maxlen=30)  # ~1 second
        self.frame_count = 0
        self.detections: list[MicroExpression] = []

    def process_frame(self, au_intensities: dict[str, float]) -> list[MicroExpression]:
        """Process a frame's AU intensities and detect micro-expressions."""
        self.au_history.append(au_intensities)
        self.frame_count += 1

        if len(self.au_history) < 3:
            return []

        new_detections = []

        for au_id in au_intensities:
            detection = self._check_micro_expression(au_id)
            if detection:
                new_detections.append(detection)
                self.detections.append(detection)

        return new_detections

    def _check_micro_expression(self, au_id: str) -> MicroExpression | None:
        """Check if a specific AU shows micro-expression pattern."""
        history = list(self.au_history)
        if len(history) < 3:
            return None

        intensities = [h.get(au_id, 0.0) for h in history]
        n = len(intensities)

        # Look for rapid onset-offset pattern in the last few frames
        # Pattern: low -> high -> low within MIN_FRAMES to MAX_FRAMES
        for end_idx in range(n - 1, max(0, n - MAX_FRAMES - 1), -1):
            if intensities[end_idx] > 0.2:
                continue  # Current frame should be low (offset)

            # Find peak
            peak_val = 0.0
            peak_idx = -1
            for mid_idx in range(end_idx - 1, max(0, end_idx - MAX_FRAMES), -1):
                if intensities[mid_idx] > peak_val:
                    peak_val = intensities[mid_idx]
                    peak_idx = mid_idx

            if peak_val < 0.4:
                continue  # Peak must be significant

            # Check onset was low
            if peak_idx <= 0:
                continue
            onset_idx = peak_idx - 1
            if intensities[onset_idx] > 0.2:
                continue

            # Duration check
            duration_frames = end_idx - onset_idx
            if duration_frames < MIN_FRAMES or duration_frames > MAX_FRAMES:
                continue

            duration_ms = duration_frames * self.frame_duration_ms

            # Determine expression type
            expr_type = AU_EMOTION_MAP.get(au_id, f"미세표정 ({au_id})")

            return MicroExpression(
                au_id=au_id,
                start_frame=self.frame_count - (n - onset_idx),
                end_frame=self.frame_count - (n - end_idx),
                duration_ms=duration_ms,
                peak_intensity=peak_val,
                expression_type=expr_type,
            )

        return None

    def get_recent_detections(self, last_n: int = 5) -> list[MicroExpression]:
        return list(self.detections)[-last_n:]

    def reset(self):
        self.au_history.clear()
        self.detections.clear()
        self.frame_count = 0
