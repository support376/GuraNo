"""Speaker separation - distinguish subject from AI/other speakers."""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SpeakerSegment:
    speaker_id: str
    start_time: float
    end_time: float
    is_subject: bool = False


class SpeakerSeparator:
    def __init__(self):
        self.tts_segments: list[tuple[float, float]] = []  # (start, end) of AI TTS
        self.subject_speaker_id: str | None = None

    def mark_tts_segment(self, start: float, end: float):
        """Mark a time segment as AI TTS output (to be excluded from analysis)."""
        self.tts_segments.append((start, end))

    def is_tts_time(self, timestamp: float) -> bool:
        """Check if a timestamp falls within a TTS segment."""
        for start, end in self.tts_segments:
            if start <= timestamp <= end:
                return True
        return False

    def filter_subject_audio(self, audio_timestamps: list[float]) -> list[bool]:
        """Return mask indicating which timestamps are subject speech (not TTS)."""
        return [not self.is_tts_time(t) for t in audio_timestamps]

    def separate_speakers_simple(self, audio_segments: list[dict]) -> list[SpeakerSegment]:
        """
        Simple speaker separation based on TTS timestamps.
        For MVP: everything not during TTS is assumed to be the subject.
        More sophisticated diarization (pyannote) can be added later.
        """
        segments = []
        for seg in audio_segments:
            ts = seg.get("timestamp", 0)
            is_tts = self.is_tts_time(ts)
            segments.append(SpeakerSegment(
                speaker_id="tts" if is_tts else "subject",
                start_time=ts,
                end_time=ts + seg.get("duration", 0.1),
                is_subject=not is_tts,
            ))
        return segments
