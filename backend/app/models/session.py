import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.database import Base


class SessionStatus(str, enum.Enum):
    SETUP = "setup"
    CALIBRATING = "calibrating"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[str] = mapped_column(SAEnum(SessionStatus), default=SessionStatus.SETUP)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Baseline values
    baseline_hr: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_hrv: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_pitch: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_speech_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    # HR source: apple_watch, ble, rppg, none
    hr_source: Mapped[str] = mapped_column(String(20), default="none")

    # Final score
    truth_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    questions: Mapped[list["Question"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    answers: Mapped[list["Answer"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    report: Mapped["Report | None"] = relationship(back_populates="session", uselist=False, cascade="all, delete-orphan")
