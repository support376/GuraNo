"""Web Speech API fallback - delegates TTS to the browser."""
from app.tts.provider import TTSProvider


class WebSpeechFallback(TTSProvider):
    """
    This provider doesn't generate audio server-side.
    Instead, it signals the frontend to use the browser's Web Speech API.
    """
    async def synthesize(self, text: str) -> bytes | None:
        return None  # Signal to use client-side TTS
