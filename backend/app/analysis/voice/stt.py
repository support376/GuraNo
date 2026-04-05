"""Speech-to-Text using Whisper for Korean."""
import logging
import tempfile
import os

import numpy as np

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000

# Lazy-load whisper to avoid import time
_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            import whisper
            logger.info("Loading Whisper model (base for MVP speed)...")
            _model = whisper.load_model("base")
            logger.info("Whisper model loaded")
        except ImportError:
            logger.warning("Whisper not installed, STT disabled")
    return _model


def transcribe(audio: np.ndarray, sr: int = SAMPLE_RATE) -> str:
    """Transcribe Korean speech to text."""
    model = _get_model()
    if model is None:
        return ""

    if len(audio) < sr * 0.5:
        return ""

    # Normalize to float32 [-1, 1]
    audio_float = audio.astype(np.float32)
    if np.max(np.abs(audio_float)) > 0:
        audio_float = audio_float / np.max(np.abs(audio_float))

    try:
        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            import soundfile as sf
            sf.write(f.name, audio_float, sr)
            temp_path = f.name

        result = model.transcribe(temp_path, language="ko", fp16=False)
        os.unlink(temp_path)

        text = result.get("text", "").strip()
        return text
    except Exception as e:
        logger.error(f"STT failed: {e}")
        return ""
