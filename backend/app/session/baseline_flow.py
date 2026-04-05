import logging
from collections import deque

import numpy as np

logger = logging.getLogger(__name__)

# Default baseline questions for calibration
BASELINE_QUESTIONS_KO = [
    {"text": "성함이 어떻게 되시나요?", "category": "baseline"},
    {"text": "생년월일을 말씀해주세요.", "category": "baseline"},
    {"text": "지금 앉아계신 의자 색상은 무엇인가요?", "category": "baseline"},
    {"text": "오늘 날씨가 어떤가요?", "category": "neutral"},
    {"text": "오늘 점심은 뭘 드셨나요?", "category": "neutral"},
]


class BaselineCollector:
    def __init__(self):
        self.hr_readings: list[float] = []
        self.pitch_readings: list[float] = []
        self.speech_rate_readings: list[float] = []
        self.is_collecting = False

    def start(self):
        self.hr_readings.clear()
        self.pitch_readings.clear()
        self.speech_rate_readings.clear()
        self.is_collecting = True

    def add_hr(self, bpm: float):
        if self.is_collecting:
            self.hr_readings.append(bpm)

    def add_voice(self, pitch: float, speech_rate: float):
        if self.is_collecting:
            if pitch > 0:
                self.pitch_readings.append(pitch)
            if speech_rate > 0:
                self.speech_rate_readings.append(speech_rate)

    def finalize(self) -> dict:
        self.is_collecting = False
        result = {
            "baseline_hr": float(np.mean(self.hr_readings)) if self.hr_readings else 72.0,
            "baseline_hr_std": float(np.std(self.hr_readings)) if len(self.hr_readings) > 1 else 5.0,
            "baseline_hrv": float(np.std(np.diff(self.hr_readings))) if len(self.hr_readings) > 2 else 40.0,
            "baseline_pitch": float(np.mean(self.pitch_readings)) if self.pitch_readings else 150.0,
            "baseline_pitch_std": float(np.std(self.pitch_readings)) if len(self.pitch_readings) > 1 else 20.0,
            "baseline_speech_rate": float(np.mean(self.speech_rate_readings)) if self.speech_rate_readings else 4.0,
        }
        logger.info(f"Baseline finalized: HR={result['baseline_hr']:.1f}, Pitch={result['baseline_pitch']:.1f}")
        return result

    @staticmethod
    def get_baseline_questions() -> list[dict]:
        return BASELINE_QUESTIONS_KO
