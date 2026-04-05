from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Database
    database_url: str = "sqlite+aiosqlite:///./gurano.db"

    # Google TTS
    google_tts_api_key: str = ""
    google_tts_language: str = "ko-KR"

    # Whisper
    whisper_model: str = "large-v3"

    # Analysis
    analysis_interval_sec: float = 2.0
    lie_threshold: float = 0.70
    suspect_threshold: float = 0.50

    # CORS
    cors_origins: str = "*"

    # Captures
    capture_dir: str = "./captures"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def capture_path(self) -> Path:
        p = Path(self.capture_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
