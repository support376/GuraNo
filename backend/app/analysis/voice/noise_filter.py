"""Noise filtering for audio using simple spectral gating as MVP fallback."""
import logging
import numpy as np

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000


def apply_noise_reduction(audio: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Simple noise reduction by zeroing low-energy frames."""
    if len(audio) < 100:
        return audio
    try:
        energy = np.abs(audio.astype(np.float64))
        threshold = np.mean(energy) * 0.3
        mask = energy > threshold
        return (audio * mask).astype(audio.dtype)
    except Exception as e:
        logger.warning(f"Noise filter failed: {e}")
        return audio


def compute_energy(audio: np.ndarray, frame_size: int = 512) -> np.ndarray:
    """Compute short-term energy for voice activity detection."""
    n_frames = len(audio) // frame_size
    energy = np.zeros(n_frames)
    for i in range(n_frames):
        frame = audio[i * frame_size:(i + 1) * frame_size].astype(np.float64)
        energy[i] = np.sum(frame ** 2) / frame_size
    return energy


def is_speech_present(audio: np.ndarray, threshold: float = 0.01) -> bool:
    """Simple VAD based on energy threshold."""
    energy = compute_energy(audio)
    if len(energy) == 0:
        return False
    return float(np.mean(energy)) > threshold
