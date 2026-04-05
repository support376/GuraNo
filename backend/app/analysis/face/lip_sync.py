"""Lip sync detection - verify the on-screen person is the one speaking."""
import logging
from collections import deque

import numpy as np

logger = logging.getLogger(__name__)


class LipSyncDetector:
    def __init__(self):
        self.mouth_open_history: deque[float] = deque(maxlen=30)
        self.audio_energy_history: deque[float] = deque(maxlen=30)

    def add_frame(self, mouth_open_ratio: float):
        """Add mouth openness from video frame."""
        self.mouth_open_history.append(mouth_open_ratio)

    def add_audio_energy(self, energy: float):
        """Add audio energy level."""
        self.audio_energy_history.append(energy)

    def is_speaking(self) -> bool:
        """Check if the on-screen person's lip movement correlates with audio."""
        if len(self.mouth_open_history) < 5 or len(self.audio_energy_history) < 5:
            return False

        mouth = np.array(list(self.mouth_open_history)[-10:])
        audio = np.array(list(self.audio_energy_history)[-10:])

        if len(mouth) != len(audio):
            min_len = min(len(mouth), len(audio))
            mouth = mouth[-min_len:]
            audio = audio[-min_len:]

        # Normalize
        mouth_norm = mouth - np.mean(mouth)
        audio_norm = audio - np.mean(audio)

        mouth_std = np.std(mouth_norm)
        audio_std = np.std(audio_norm)

        if mouth_std < 1e-6 or audio_std < 1e-6:
            return False

        # Correlation
        correlation = float(np.corrcoef(mouth_norm, audio_norm)[0, 1])

        # Positive correlation > 0.3 suggests the face is speaking
        return correlation > 0.3

    def get_correlation(self) -> float:
        """Get the current lip-audio correlation value."""
        if len(self.mouth_open_history) < 5 or len(self.audio_energy_history) < 5:
            return 0.0

        mouth = np.array(list(self.mouth_open_history)[-10:])
        audio = np.array(list(self.audio_energy_history)[-10:])

        min_len = min(len(mouth), len(audio))
        mouth = mouth[-min_len:]
        audio = audio[-min_len:]

        mouth_std = np.std(mouth)
        audio_std = np.std(audio)
        if mouth_std < 1e-6 or audio_std < 1e-6:
            return 0.0

        return float(np.corrcoef(mouth, audio)[0, 1])
