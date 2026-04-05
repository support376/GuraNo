"""Report generator - creates comprehensive analysis reports."""
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.models.question import Question
from app.models.answer import Answer
from app.models.report import Report

logger = logging.getLogger(__name__)


async def generate_full_report(session_id: str, db: AsyncSession) -> dict:
    """Generate a full report from session data."""
    # Load session
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "Session not found"}

    # Load questions
    q_result = await db.execute(
        select(Question).where(Question.session_id == session_id).order_by(Question.order)
    )
    questions = {q.id: q for q in q_result.scalars().all()}

    # Load answers
    a_result = await db.execute(
        select(Answer).where(Answer.session_id == session_id).order_by(Answer.timestamp)
    )
    answers = a_result.scalars().all()

    # Build report data
    question_results = []
    for answer in answers:
        q = questions.get(answer.question_id)
        question_results.append({
            "question_number": q.order if q else 0,
            "question_text": q.text if q else "",
            "answer_text": answer.transcript or "",
            "verdict": answer.verdict,
            "confidence": answer.fusion_score,
            "voice_score": answer.voice_score,
            "face_score": answer.face_score,
            "hr_score": answer.hr_score,
            "hr_bpm": answer.hr_bpm,
            "reasons": answer.reasons.get("reasons", []) if answer.reasons else [],
            "screenshot_path": answer.screenshot_path,
        })

    return {
        "session_id": session_id,
        "created_at": session.created_at.isoformat() if session.created_at else "",
        "truth_score": session.truth_score,
        "baseline_hr": session.baseline_hr,
        "question_results": question_results,
    }
