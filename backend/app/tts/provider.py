"""TTS provider interface and factory."""
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> bytes | None:
        """Synthesize text to audio bytes (WAV/MP3). Returns None if using client-side TTS."""
        pass


class WebSpeechTTS(TTSProvider):
    """Fallback: instruct the client to use Web Speech API (no server-side synthesis)."""
    async def synthesize(self, text: str) -> bytes | None:
        # Return None to signal client-side TTS should be used
        return None


def get_tts_provider() -> TTSProvider:
    """Get the configured TTS provider."""
    from app.config import settings

    if settings.google_tts_api_key:
        try:
            from app.tts.google_tts import GoogleTTS
            return GoogleTTS()
        except ImportError:
            logger.warning("Google TTS not available, using Web Speech API")

    return WebSpeechTTS()
