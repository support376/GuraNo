"""Heart rate baseline management."""
import logging
import numpy as np

logger = logging.getLogger(__name__)


class HRBaseline:
    def __init__(self):
        self.readings: list[float] = []
        self.is_collecting = False

        # Baseline values
        self.mean_hr: float = 72.0
        self.std_hr: float = 5.0
        self.mean_hrv: float = 40.0

    def start_collection(self):
        self.readings.clear()
        self.is_collecting = True

    def add_reading(self, bpm: float):
        if self.is_collecting and 40 <= bpm <= 200:
            self.readings.append(bpm)

    def finalize(self) -> dict:
        self.is_collecting = False
        if len(self.readings) >= 5:
            self.mean_hr = float(np.mean(self.readings))
            self.std_hr = max(float(np.std(self.readings)), 2.0)
            # Approximate HRV from beat-to-beat variation
            if len(self.readings) > 2:
                diffs = np.diff(self.readings)
                self.mean_hrv = float(np.sqrt(np.mean(diffs ** 2)))
            else:
                self.mean_hrv = 40.0
        logger.info(f"HR Baseline: mean={self.mean_hr:.1f}, std={self.std_hr:.1f}, hrv={self.mean_hrv:.1f}")
        return {
            "baseline_hr": self.mean_hr,
            "baseline_hr_std": self.std_hr,
            "baseline_hrv": self.mean_hrv,
        }

    def compute_zscore(self, bpm: float) -> float:
        if self.std_hr < 0.1:
            return 0.0
        return (bpm - self.mean_hr) / self.std_hr
