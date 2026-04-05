"""Google Cloud Text-to-Speech provider."""
import logging
import os
import hashlib

from app.tts.provider import TTSProvider
from app.config import settings

logger = logging.getLogger(__name__)


class GoogleTTS(TTSProvider):
    def __init__(self):
        self.cache_dir = os.path.join(settings.capture_dir, "tts_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    async def synthesize(self, text: str) -> bytes | None:
        # Check cache first
        cache_key = hashlib.md5(text.encode()).hexdigest()
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.mp3")

        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                return f.read()

        try:
            from google.cloud import texttospeech

            client = texttospeech.TextToSpeechClient()
            synthesis_input = texttospeech.SynthesisInput(text=text)

            voice = texttospeech.VoiceSelectionParams(
                language_code=settings.google_tts_language,
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
            )

            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.9,
            )

            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            # Cache
            with open(cache_path, "wb") as f:
                f.write(response.audio_content)

            return response.audio_content
        except Exception as e:
            logger.error(f"Google TTS failed: {e}")
            return None
