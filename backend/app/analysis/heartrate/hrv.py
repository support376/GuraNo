"""Heart Rate Variability (HRV) computation from HR readings."""
import numpy as np


class HRVCalculator:
    @staticmethod
    def compute(hr_readings: list[float]) -> dict:
        """Compute HRV metrics from a series of HR readings (1Hz)."""
        if len(hr_readings) < 3:
            return {"rmssd": 0.0, "sdnn": 0.0, "pnn50": 0.0, "mean_hr": 0.0}

        arr = np.array(hr_readings)

        # Convert HR to approximate RR intervals (ms)
        rr_intervals = 60000.0 / arr  # ms per beat

        # SDNN: Standard deviation of NN intervals
        sdnn = float(np.std(rr_intervals))

        # RMSSD: Root mean square of successive differences
        diffs = np.diff(rr_intervals)
        rmssd = float(np.sqrt(np.mean(diffs ** 2)))

        # pNN50: Percentage of successive differences > 50ms
        pnn50 = float(np.sum(np.abs(diffs) > 50) / len(diffs) * 100) if len(diffs) > 0 else 0.0

        return {
            "rmssd": rmssd,
            "sdnn": sdnn,
            "pnn50": pnn50,
            "mean_hr": float(np.mean(arr)),
        }
