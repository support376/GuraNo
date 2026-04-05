"""Heart Rate Analyzer - combines baseline, HRV, and scoring."""
import logging
import time
from collections import deque

from app.analysis.heartrate.baseline import HRBaseline
from app.analysis.heartrate.hrv import HRVCalculator

logger = logging.getLogger(__name__)


class HRAnalyzer:
    def __init__(self):
        self.baseline = HRBaseline()
        self.hrv_calc = HRVCalculator()
        self.readings: deque[tuple[float, float]] = deque(maxlen=300)  # (bpm, timestamp)
        self.recent_window: list[float] = []  # last 10 readings for HRV

    @property
    def baseline_hr(self) -> float:
        return self.baseline.mean_hr

    @property
    def baseline_hrv(self) -> float:
        return self.baseline.mean_hrv

    def start_baseline_collection(self):
        self.baseline.start_collection()

    def add_baseline_reading(self, bpm: float):
        self.baseline.add_reading(bpm)

    def finalize_baseline(self):
        self.baseline.finalize()

    def add_reading(self, bpm: float, ts: float):
        self.readings.append((bpm, ts))
        self.recent_window.append(bpm)
        if len(self.recent_window) > 30:
            self.recent_window = self.recent_window[-30:]

    def get_current_scores(self) -> dict:
        if len(self.recent_window) < 3:
            return {"lie_probability": 0.0, "hr_bpm": 0.0, "zscore": 0.0, "hrv": {}}

        current_bpm = self.recent_window[-1] if self.recent_window else 0.0
        zscore = self.baseline.compute_zscore(current_bpm)
        hrv = self.hrv_calc.compute(self.recent_window[-10:])

        # Score based on Z-score and HRV changes
        # Higher Z-score = higher lie probability
        # Lower HRV (RMSSD) compared to baseline = higher lie probability
        hr_lie_score = 0.0

        # Z-score contribution (0 to 0.5)
        if zscore > 0:
            hr_lie_score += min(zscore / 3.0, 0.5)  # z=1.5 -> 0.25, z=3.0 -> 0.5

        # HRV drop contribution (0 to 0.3)
        if self.baseline.mean_hrv > 0 and hrv["rmssd"] > 0:
            hrv_ratio = hrv["rmssd"] / self.baseline.mean_hrv
            if hrv_ratio < 1.0:
                hr_lie_score += (1.0 - hrv_ratio) * 0.3

        # HR elevation contribution (0 to 0.2)
        hr_increase = current_bpm - self.baseline.mean_hr
        if hr_increase > 5:
            hr_lie_score += min(hr_increase / 50.0, 0.2)

        hr_lie_score = min(max(hr_lie_score, 0.0), 1.0)

        return {
            "lie_probability": hr_lie_score,
            "hr_bpm": current_bpm,
            "zscore": zscore,
            "hrv": hrv,
            "hr_increase": current_bpm - self.baseline.mean_hr,
        }
