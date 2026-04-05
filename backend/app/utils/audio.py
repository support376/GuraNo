"""Audio utility functions."""
import numpy as np


def pcm16_to_float32(pcm_bytes: bytes) -> np.ndarray:
    """Convert PCM 16-bit bytes to float32 numpy array."""
    audio = np.frombuffer(pcm_bytes, dtype=np.int16)
    return audio.astype(np.float32) / 32768.0


def float32_to_pcm16(audio: np.ndarray) -> bytes:
    """Convert float32 numpy array to PCM 16-bit bytes."""
    audio = np.clip(audio, -1.0, 1.0)
    return (audio * 32767).astype(np.int16).tobytes()


def resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """Simple resampling by linear interpolation."""
    if orig_sr == target_sr:
        return audio
    ratio = target_sr / orig_sr
    new_length = int(len(audio) * ratio)
    indices = np.linspace(0, len(audio) - 1, new_length)
    return np.interp(indices, np.arange(len(audio)), audio)
