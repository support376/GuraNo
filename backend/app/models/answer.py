import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"))
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Transcript
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Per-modality scores
    voice_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    face_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    hr_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fusion_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Verdict: truth, suspect, lie
    verdict: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Heart rate at answer time
    hr_bpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    hr_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    hr_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    hrv_rmssd: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Explanation reasons (JSON list of strings)
    reasons: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Screenshot path if lie detected
    screenshot_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    clip_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Voice features snapshot
    voice_features: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Face features snapshot
    face_features: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    session: Mapped["Session"] = relationship(back_populates="answers")
