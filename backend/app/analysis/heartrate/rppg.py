"""
Remote Photoplethysmography (rPPG) - Estimate heart rate from webcam video.
Uses the green channel intensity changes in facial skin regions.

Algorithm: POS (Plane-Orthogonal-to-Skin) method simplified for MVP.
"""
import logging
from collections import deque

import cv2
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks

logger = logging.getLogger(__name__)

# Bandpass filter for HR range: 0.7-4 Hz (42-240 BPM)
LOWCUT = 0.7
HIGHCUT = 4.0
SAMPLE_RATE = 30  # assumed fps


def butter_bandpass(lowcut: float, highcut: float, fs: float, order: int = 4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


class RPPGEstimator:
    def __init__(self, buffer_seconds: int = 10):
        self.buffer_size = buffer_seconds * SAMPLE_RATE
        self.green_signal: deque[float] = deque(maxlen=self.buffer_size)
        self.timestamps: deque[float] = deque(maxlen=self.buffer_size)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.latest_bpm = 0.0

    def process_frame(self, frame: np.ndarray, timestamp: float) -> float | None:
        """Extract green channel mean from face ROI and estimate HR."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))

        if len(faces) == 0:
            return None

        # Use largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

        # ROI: forehead region (top 30% of face, middle 60% width)
        roi_x = x + int(w * 0.2)
        roi_y = y + int(h * 0.05)
        roi_w = int(w * 0.6)
        roi_h = int(h * 0.3)

        roi = frame[roi_y:roi_y + roi_h, roi_x:roi_x + roi_w]
        if roi.size == 0:
            return None

        # Extract green channel mean
        green_mean = float(np.mean(roi[:, :, 1]))
        self.green_signal.append(green_mean)
        self.timestamps.append(timestamp)

        # Need at least 5 seconds of data
        if len(self.green_signal) < SAMPLE_RATE * 5:
            return None

        return self._estimate_hr()

    def _estimate_hr(self) -> float:
        signal = np.array(self.green_signal)

        # Detrend
        signal = signal - np.mean(signal)

        # Normalize
        std = np.std(signal)
        if std < 1e-6:
            return self.latest_bpm
        signal = signal / std

        # Bandpass filter
        try:
            b, a = butter_bandpass(LOWCUT, HIGHCUT, SAMPLE_RATE)
            filtered = filtfilt(b, a, signal)
        except Exception:
            return self.latest_bpm

        # FFT to find dominant frequency
        n = len(filtered)
        fft_vals = np.abs(np.fft.rfft(filtered))
        freqs = np.fft.rfftfreq(n, d=1.0 / SAMPLE_RATE)

        # Only look in HR range
        mask = (freqs >= LOWCUT) & (freqs <= HIGHCUT)
        if not np.any(mask):
            return self.latest_bpm

        fft_hr = fft_vals[mask]
        freqs_hr = freqs[mask]

        peak_idx = np.argmax(fft_hr)
        peak_freq = freqs_hr[peak_idx]
        bpm = peak_freq * 60.0

        # Sanity check
        if 40 <= bpm <= 200:
            self.latest_bpm = bpm

        return self.latest_bpm

    def reset(self):
        self.green_signal.clear()
        self.timestamps.clear()
        self.latest_bpm = 0.0
