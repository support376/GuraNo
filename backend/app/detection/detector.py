"""Lie Detector - main detection logic and recording."""
import json
import logging
from datetime import datetime

from fastapi import WebSocket

from app.detection.capture import save_screenshot, save_clip
from app.detection.explanation import generate_reasons
from app.db.database import async_session
from app.models.answer import Answer
from app.models.report import Report
from app.models.session import Session, SessionStatus

logger = logging.getLogger(__name__)


class LieDetector:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.answers: list[dict] = []
        self.hr_timeline: list[dict] = []

    async def on_lie_detected(
        self,
        frame_data: bytes,
        frame_buffer: list,
        fusion_score: float,
        voice_result: dict,
        face_result: dict,
        hr_result: dict,
        transcript: str,
        question: str,
        question_id: str,
        ts: float,
        ws: WebSocket,
    ):
        """Handle a lie detection event."""
        # Save screenshot
        screenshot_url = save_screenshot(frame_data, self.session_id, ts)

        # Save video clip (last 2 seconds from buffer)
        recent_frames = [(f, t) for f, t in frame_buffer if abs(t - ts) <= 2.0]
        clip_url = save_clip(recent_frames, self.session_id, ts)

        # Generate reasons
        reasons = generate_reasons(voice_result, face_result, hr_result, fusion_score)

        # Send lie detection event to frontend
        await ws.send_text(json.dumps({
            "type": "lie_detected",
            "ts": ts,
            "confidence": fusion_score,
            "screenshot_url": screenshot_url,
            "clip_url": clip_url,
            "transcript": transcript,
            "question": question,
            "reasons": reasons,
        }, ensure_ascii=False))

        logger.info(f"Lie detected: confidence={fusion_score:.2f}, reasons={reasons}")

    def record_analysis(
        self,
        question_id: str,
        voice_result: dict,
        face_result: dict,
        hr_result: dict,
        fusion_result: dict,
        verdict: str,
        transcript: str,
        hr_bpm: float,
    ):
        """Record analysis result for a question."""
        existing = next((a for a in self.answers if a["question_id"] == question_id), None)

        record = {
            "question_id": question_id,
            "voice_score": voice_result.get("lie_probability", 0),
            "face_score": face_result.get("lie_probability", 0),
            "hr_score": hr_result.get("lie_probability", 0),
            "fusion_score": fusion_result.get("fusion_score", 0),
            "verdict": verdict,
            "transcript": transcript,
            "hr_bpm": hr_bpm,
            "voice_features": voice_result.get("features", {}),
            "face_features": {
                "fake_smile": face_result.get("fake_smile", False),
                "micro_expressions": face_result.get("micro_expressions", []),
                "blink_rate": face_result.get("blink_rate", 0),
            },
            "reasons": generate_reasons(voice_result, face_result, hr_result, fusion_result.get("fusion_score", 0)),
        }

        if existing:
            # Update with latest (keep worst score)
            if record["fusion_score"] > existing["fusion_score"]:
                self.answers[self.answers.index(existing)] = record
        else:
            self.answers.append(record)

        # HR timeline
        self.hr_timeline.append({
            "ts": datetime.utcnow().timestamp(),
            "bpm": hr_bpm,
            "question_id": question_id,
        })

    async def generate_report(self) -> dict:
        """Generate final report and save to database."""
        if not self.answers:
            return {"error": "No answers recorded"}

        lie_count = sum(1 for a in self.answers if a["verdict"] == "거짓")
        suspect_count = sum(1 for a in self.answers if a["verdict"] == "의심")
        truth_count = sum(1 for a in self.answers if a["verdict"] == "진실")
        total = len(self.answers)

        truth_score = ((truth_count + suspect_count * 0.5) / total * 100) if total > 0 else 0

        # HR stats
        hr_values = [(a["hr_bpm"], a["question_id"]) for a in self.answers if a.get("hr_bpm", 0) > 0]
        hr_peak = max(hr_values, key=lambda x: x[0]) if hr_values else (0, "")
        hr_lowest = min(hr_values, key=lambda x: x[0]) if hr_values else (0, "")

        # Save to DB
        async with async_session() as db:
            # Save answers
            for a in self.answers:
                answer = Answer(
                    session_id=self.session_id,
                    question_id=a["question_id"],
                    transcript=a.get("transcript"),
                    voice_score=a["voice_score"],
                    face_score=a["face_score"],
                    hr_score=a["hr_score"],
                    fusion_score=a["fusion_score"],
                    verdict=a["verdict"],
                    hr_bpm=a.get("hr_bpm"),
                    reasons={"reasons": a.get("reasons", [])},
                    voice_features=a.get("voice_features"),
                    face_features=a.get("face_features"),
                )
                db.add(answer)

            # Save report
            report = Report(
                session_id=self.session_id,
                truth_score=truth_score,
                total_questions=total,
                lie_count=lie_count,
                suspect_count=suspect_count,
                truth_count=truth_count,
                hr_peak_bpm=hr_peak[0] if hr_peak else None,
                hr_peak_question=hr_peak[1] if hr_peak else None,
                hr_lowest_bpm=hr_lowest[0] if hr_lowest else None,
                hr_lowest_question=hr_lowest[1] if hr_lowest else None,
                modality_weights={"voice": 0.30, "face": 0.30, "hr": 0.40},
                hr_timeline={
                    "timestamps": [h["ts"] for h in self.hr_timeline],
                    "bpm": [h["bpm"] for h in self.hr_timeline],
                    "questions": [h["question_id"] for h in self.hr_timeline],
                },
            )
            db.add(report)

            # Update session
            from sqlalchemy import select
            result = await db.execute(select(Session).where(Session.id == self.session_id))
            session = result.scalar_one_or_none()
            if session:
                session.status = SessionStatus.COMPLETED
                session.truth_score = truth_score
                session.completed_at = datetime.utcnow()

            await db.commit()

        return {
            "report_id": report.id if report else None,
            "truth_score": truth_score,
            "total_questions": total,
            "lie_count": lie_count,
            "suspect_count": suspect_count,
            "truth_count": truth_count,
        }
