"""Voice Analyzer - main class integrating all voice analysis components."""
import logging
import numpy as np

from app.analysis.voice.noise_filter import apply_noise_reduction, is_speech_present
from app.analysis.voice.features import extract_features
from app.analysis.voice.stt import transcribe
from app.analysis.voice.korean_utils import analyze_transcript
from app.analysis.voice.speaker import SpeakerSeparator

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000


class VoiceAnalyzer:
    def __init__(self):
        self.speaker_separator = SpeakerSeparator()
        self.latest_features: dict = {}
        self.latest_transcript: str = ""
        self.baseline_pitch: float = 150.0
        self.baseline_speech_rate: float = 4.0
        self.baseline_pitch_std: float = 20.0

        # Baseline collection
        self._baseline_pitches: list[float] = []
        self._baseline_rates: list[float] = []
        self._is_collecting_baseline = False

    async def initialize(self):
        logger.info("VoiceAnalyzer initialized")

    def start_baseline_collection(self):
        self._baseline_pitches.clear()
        self._baseline_rates.clear()
        self._is_collecting_baseline = True

    def finalize_baseline(self):
        self._is_collecting_baseline = False
        if self._baseline_pitches:
            self.baseline_pitch = float(np.mean(self._baseline_pitches))
            self.baseline_pitch_std = max(float(np.std(self._baseline_pitches)), 5.0)
        if self._baseline_rates:
            self.baseline_speech_rate = float(np.mean(self._baseline_rates))
        logger.info(f"Voice baseline: pitch={self.baseline_pitch:.1f}, rate={self.baseline_speech_rate:.1f}")

    async def process_chunk(self, audio_bytes: bytes, timestamp: float):
        """Process an audio chunk (PCM 16bit 16kHz mono)."""
        audio = np.frombuffer(audio_bytes, dtype=np.int16)

        # Noise reduction
        audio_clean = apply_noise_reduction(audio)

        # Check if speech is present
        if not is_speech_present(audio_clean):
            return

        # Skip if during TTS playback
        if self.speaker_separator.is_tts_time(timestamp):
            return

        # Extract features
        features = extract_features(audio_clean, SAMPLE_RATE)
        self.latest_features = features

        # Baseline collection
        if self._is_collecting_baseline:
            if features["f0_mean"] > 0:
                self._baseline_pitches.append(features["f0_mean"])
            if features["speech_rate"] > 0:
                self._baseline_rates.append(features["speech_rate"])

        # STT
        transcript = transcribe(audio_clean, SAMPLE_RATE)
        if transcript:
            self.latest_transcript = transcript

    def get_current_scores(self) -> dict:
        """Compute lie probability from current voice features."""
        f = self.latest_features
        if not f or f.get("f0_mean", 0) == 0:
            return {"lie_probability": 0.0, "features": {}, "transcript_analysis": {}}

        lie_score = 0.0

        # Pitch deviation from baseline (0 to 0.3)
        if self.baseline_pitch > 0 and f["f0_mean"] > 0:
            pitch_change = (f["f0_mean"] - self.baseline_pitch) / self.baseline_pitch
            if pitch_change > 0.05:  # 5%+ increase
                lie_score += min(pitch_change * 2, 0.3)

        # Pause analysis (0 to 0.25)
        if f.get("pause_max_duration", 0) > 1.5:
            lie_score += min(f["pause_max_duration"] / 8.0, 0.25)

        # Speech rate decrease (0 to 0.2)
        if self.baseline_speech_rate > 0 and f.get("speech_rate", 0) > 0:
            rate_change = (self.baseline_speech_rate - f["speech_rate"]) / self.baseline_speech_rate
            if rate_change > 0.1:  # 10%+ decrease
                lie_score += min(rate_change, 0.2)

        # Jitter increase (0 to 0.15)
        if f.get("jitter", 0) > 0.02:
            lie_score += min(f["jitter"] * 3, 0.15)

        # Filler/hesitation from transcript (0 to 0.1)
        if self.latest_transcript:
            t_analysis = analyze_transcript(self.latest_transcript, f.get("total_duration", 1.0))
            filler_ratio = t_analysis["filler_count"] / max(t_analysis["word_count"], 1)
            if filler_ratio > 0.15:
                lie_score += 0.1
        else:
            t_analysis = {}

        lie_score = min(max(lie_score, 0.0), 1.0)

        return {
            "lie_probability": lie_score,
            "features": f,
            "transcript_analysis": t_analysis,
            "pitch_change_pct": ((f["f0_mean"] - self.baseline_pitch) / self.baseline_pitch * 100) if self.baseline_pitch > 0 else 0,
        }
