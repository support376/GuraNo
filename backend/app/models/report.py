import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Summary
    truth_score: Mapped[float] = mapped_column(Float)
    total_questions: Mapped[int] = mapped_column(Integer)
    lie_count: Mapped[int] = mapped_column(Integer, default=0)
    suspect_count: Mapped[int] = mapped_column(Integer, default=0)
    truth_count: Mapped[int] = mapped_column(Integer, default=0)

    # HR summary
    hr_peak_bpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    hr_peak_question: Mapped[str | None] = mapped_column(String(500), nullable=True)
    hr_lowest_bpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    hr_lowest_question: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Modality contribution
    modality_weights: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # HR timeline data (for chart)
    hr_timeline: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # PDF path
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    session: Mapped["Session"] = relationship(back_populates="report")
