"""Voice feature extraction using acoustic analysis."""
import logging
import io

import numpy as np

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000


def extract_features(audio: np.ndarray, sr: int = SAMPLE_RATE) -> dict:
    """
    Extract acoustic features relevant to deception detection.
    Uses basic numpy/scipy instead of openSMILE for MVP portability.
    """
    if len(audio) < sr * 0.5:  # less than 0.5s
        return _empty_features()

    audio_float = audio.astype(np.float64)
    if np.max(np.abs(audio_float)) > 0:
        audio_float = audio_float / np.max(np.abs(audio_float))

    features = {}

    # Pitch (F0) estimation using autocorrelation
    features.update(_extract_pitch(audio_float, sr))

    # Temporal features
    features.update(_extract_temporal(audio_float, sr))

    # Voice quality
    features.update(_extract_quality(audio_float, sr))

    # Energy
    features["energy_mean"] = float(np.mean(audio_float ** 2))
    features["energy_std"] = float(np.std(audio_float ** 2))

    return features


def _extract_pitch(audio: np.ndarray, sr: int) -> dict:
    """Estimate F0 using autocorrelation method."""
    frame_size = int(sr * 0.03)  # 30ms frames
    hop = int(sr * 0.01)  # 10ms hop
    pitches = []

    for i in range(0, len(audio) - frame_size, hop):
        frame = audio[i:i + frame_size]
        # Autocorrelation
        corr = np.correlate(frame, frame, mode='full')
        corr = corr[len(corr) // 2:]

        # Find first peak after min_lag (50Hz = sr/50)
        min_lag = sr // 500  # max 500Hz
        max_lag = sr // 50   # min 50Hz

        if max_lag > len(corr):
            continue

        segment = corr[min_lag:max_lag]
        if len(segment) == 0 or np.max(segment) < 0.1:
            continue

        peak_idx = np.argmax(segment) + min_lag
        if peak_idx > 0:
            f0 = sr / peak_idx
            if 50 <= f0 <= 500:
                pitches.append(f0)

    if not pitches:
        return {"f0_mean": 0.0, "f0_std": 0.0, "f0_range": 0.0}

    return {
        "f0_mean": float(np.mean(pitches)),
        "f0_std": float(np.std(pitches)),
        "f0_range": float(np.max(pitches) - np.min(pitches)),
    }


def _extract_temporal(audio: np.ndarray, sr: int) -> dict:
    """Extract temporal features: speech rate, pause patterns."""
    # Simple energy-based speech/silence segmentation
    frame_size = int(sr * 0.02)  # 20ms
    n_frames = len(audio) // frame_size
    energy = np.array([
        np.sum(audio[i * frame_size:(i + 1) * frame_size] ** 2) / frame_size
        for i in range(n_frames)
    ])

    threshold = np.mean(energy) * 0.3
    is_speech = energy > threshold

    # Speech rate approximation (transitions from silence to speech)
    transitions = np.diff(is_speech.astype(int))
    speech_onsets = np.sum(transitions == 1)

    # Duration
    total_duration = len(audio) / sr
    speech_frames = np.sum(is_speech)
    speech_duration = speech_frames * 0.02

    # Pause analysis
    silence_runs = []
    current_run = 0
    for s in is_speech:
        if not s:
            current_run += 1
        else:
            if current_run > 0:
                silence_runs.append(current_run * 0.02)
            current_run = 0

    return {
        "speech_rate": speech_onsets / total_duration if total_duration > 0 else 0.0,
        "speech_ratio": speech_duration / total_duration if total_duration > 0 else 0.0,
        "total_duration": total_duration,
        "pause_count": len(silence_runs),
        "pause_mean_duration": float(np.mean(silence_runs)) if silence_runs else 0.0,
        "pause_max_duration": float(np.max(silence_runs)) if silence_runs else 0.0,
    }


def _extract_quality(audio: np.ndarray, sr: int) -> dict:
    """Extract voice quality features (jitter, shimmer approximation)."""
    # Simplified jitter: variation in pitch period
    frame_size = int(sr * 0.03)
    hop = int(sr * 0.01)
    periods = []

    for i in range(0, len(audio) - frame_size, hop):
        frame = audio[i:i + frame_size]
        # Zero crossing rate as a proxy
        zcr = np.sum(np.abs(np.diff(np.sign(frame)))) / (2 * len(frame))
        if zcr > 0:
            periods.append(1.0 / (zcr * sr) if zcr * sr > 0 else 0)

    jitter = float(np.std(periods) / np.mean(periods)) if periods and np.mean(periods) > 0 else 0.0

    # Shimmer: variation in amplitude
    frame_energies = []
    for i in range(0, len(audio) - frame_size, hop):
        frame = audio[i:i + frame_size]
        frame_energies.append(np.sqrt(np.mean(frame ** 2)))

    shimmer = float(np.std(frame_energies) / np.mean(frame_energies)) if frame_energies and np.mean(frame_energies) > 0 else 0.0

    # HNR approximation
    hnr = 0.0
    if len(audio) > frame_size:
        signal_power = np.mean(audio ** 2)
        # Estimate noise from high-frequency content
        noise = np.diff(audio)
        noise_power = np.mean(noise ** 2)
        if noise_power > 0:
            hnr = 10 * np.log10(signal_power / noise_power + 1e-10)

    return {
        "jitter": jitter,
        "shimmer": shimmer,
        "hnr": hnr,
    }


def _empty_features() -> dict:
    return {
        "f0_mean": 0.0, "f0_std": 0.0, "f0_range": 0.0,
        "speech_rate": 0.0, "speech_ratio": 0.0, "total_duration": 0.0,
        "pause_count": 0, "pause_mean_duration": 0.0, "pause_max_duration": 0.0,
        "jitter": 0.0, "shimmer": 0.0, "hnr": 0.0,
        "energy_mean": 0.0, "energy_std": 0.0,
    }
