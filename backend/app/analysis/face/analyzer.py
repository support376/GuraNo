"""Face Analyzer - main class integrating all face analysis components."""
import logging

import cv2
import numpy as np

from app.analysis.face.landmarks import detect_landmarks, compute_face_metrics
from app.analysis.face.action_units import detect_action_units, check_fake_smile
from app.analysis.face.micro_expression import MicroExpressionDetector
from app.analysis.face.eye_tracker import EyeTracker
from app.analysis.face.lip_sync import LipSyncDetector

logger = logging.getLogger(__name__)


class FaceAnalyzer:
    def __init__(self):
        self.micro_detector = MicroExpressionDetector()
        self.eye_tracker = EyeTracker()
        self.lip_sync = LipSyncDetector()

        self.baseline_metrics: dict | None = None
        self._baseline_frames: list[dict] = []
        self._is_collecting_baseline = False

    async def initialize(self):
        logger.info("FaceAnalyzer initialized")

    def start_baseline_collection(self):
        self._baseline_frames.clear()
        self._is_collecting_baseline = True

    def finalize_baseline(self):
        self._is_collecting_baseline = False
        if self._baseline_frames:
            # Average baseline metrics
            self.baseline_metrics = {}
            keys = self._baseline_frames[0].keys()
            for key in keys:
                vals = [f[key] for f in self._baseline_frames if key in f and isinstance(f[key], (int, float))]
                if vals:
                    self.baseline_metrics[key] = float(np.mean(vals))
        logger.info(f"Face baseline set with {len(self._baseline_frames)} frames")

    async def analyze_frame(self, frame_data: bytes) -> dict:
        """Analyze a single video frame for deception indicators."""
        # Decode JPEG
        frame_array = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        if frame is None:
            return {"lie_probability": 0.0}

        # Detect landmarks
        points = detect_landmarks(frame)
        if not points:
            return {"lie_probability": 0.0, "face_detected": False}

        # Compute metrics
        metrics = compute_face_metrics(points)

        # Baseline collection
        if self._is_collecting_baseline:
            self._baseline_frames.append(metrics)
            return {"lie_probability": 0.0, "metrics": metrics}

        # Detect Action Units
        aus = detect_action_units(metrics, self.baseline_metrics)
        au_dict = {a.au_id: a.intensity for a in aus}

        # Check for fake smile
        fake_smile = check_fake_smile(aus)

        # Detect micro-expressions
        micro_exprs = self.micro_detector.process_frame(au_dict)

        # Eye tracking
        self.eye_tracker.process_frame(metrics, 0)
        blink_rate = self.eye_tracker.get_blink_rate()
        gaze_stability = self.eye_tracker.get_gaze_stability()

        # Lip sync
        self.lip_sync.add_frame(metrics.get("mouth_open_ratio", 0))

        # Compute lie probability
        lie_score = self._compute_score(aus, fake_smile, micro_exprs, blink_rate, gaze_stability, metrics)

        return {
            "lie_probability": lie_score,
            "face_detected": True,
            "action_units": {a.au_id: {"intensity": a.intensity, "active": a.active} for a in aus},
            "fake_smile": fake_smile,
            "micro_expressions": [
                {"au": m.au_id, "duration_ms": m.duration_ms, "type": m.expression_type}
                for m in micro_exprs
            ],
            "blink_rate": blink_rate,
            "gaze_stability": gaze_stability,
            "mouth_asymmetry": metrics.get("mouth_asymmetry", 0),
        }

    def _compute_score(self, aus, fake_smile, micro_exprs, blink_rate, gaze_stability, metrics) -> float:
        score = 0.0

        # Fake smile (0 to 0.25)
        if fake_smile:
            score += 0.25

        # Micro-expressions (0 to 0.25)
        if micro_exprs:
            score += min(len(micro_exprs) * 0.12, 0.25)

        # Blink rate deviation (normal: 15-20/min, stressed: >25/min)
        if blink_rate > 25:
            score += min((blink_rate - 25) / 40, 0.15)

        # Gaze instability (0 to 0.15)
        score += (1.0 - gaze_stability) * 0.15

        # Facial asymmetry (0 to 0.1)
        asymmetry = metrics.get("mouth_asymmetry", 0)
        if asymmetry > 0.15:
            score += min(asymmetry * 0.5, 0.1)

        # AU4 (cognitive load) (0 to 0.1)
        au4 = next((a for a in aus if a.au_id == "AU4"), None)
        if au4 and au4.intensity > 0.3:
            score += au4.intensity * 0.1

        return min(max(score, 0.0), 1.0)
