from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.database import get_db
from app.models.report import Report
from app.models.answer import Answer

router = APIRouter()


class AnswerSummary(BaseModel):
    question_id: str
    transcript: str | None = None
    voice_score: float | None = None
    face_score: float | None = None
    hr_score: float | None = None
    fusion_score: float | None = None
    verdict: str | None = None
    hr_bpm: float | None = None
    reasons: dict | None = None
    screenshot_path: str | None = None

    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    id: str
    session_id: str
    truth_score: float
    total_questions: int
    lie_count: int
    suspect_count: int
    truth_count: int
    hr_peak_bpm: float | None = None
    hr_peak_question: str | None = None
    hr_lowest_bpm: float | None = None
    hr_lowest_question: str | None = None
    modality_weights: dict | None = None
    hr_timeline: dict | None = None
    pdf_path: str | None = None
    answers: list[AnswerSummary] = []

    model_config = {"from_attributes": True}


@router.get("/session/{session_id}", response_model=ReportResponse)
async def get_report(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.session_id == session_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    answers_result = await db.execute(
        select(Answer).where(Answer.session_id == session_id).order_by(Answer.timestamp)
    )
    answers = answers_result.scalars().all()

    return ReportResponse(
        id=report.id,
        session_id=report.session_id,
        truth_score=report.truth_score,
        total_questions=report.total_questions,
        lie_count=report.lie_count,
        suspect_count=report.suspect_count,
        truth_count=report.truth_count,
        hr_peak_bpm=report.hr_peak_bpm,
        hr_peak_question=report.hr_peak_question,
        hr_lowest_bpm=report.hr_lowest_bpm,
        hr_lowest_question=report.hr_lowest_question,
        modality_weights=report.modality_weights,
        hr_timeline=report.hr_timeline,
        pdf_path=report.pdf_path,
        answers=[AnswerSummary(
            question_id=a.question_id,
            transcript=a.transcript,
            voice_score=a.voice_score,
            face_score=a.face_score,
            hr_score=a.hr_score,
            fusion_score=a.fusion_score,
            verdict=a.verdict,
            hr_bpm=a.hr_bpm,
            reasons=a.reasons,
            screenshot_path=a.screenshot_path,
        ) for a in answers],
    )


@router.get("/session/{session_id}/pdf")
async def download_pdf(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.session_id == session_id))
    report = result.scalar_one_or_none()
    if not report or not report.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(report.pdf_path, media_type="application/pdf", filename=f"gurano_report_{session_id}.pdf")
