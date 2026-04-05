from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.database import get_db
from app.models.session import Session, SessionStatus

router = APIRouter()


class SessionCreate(BaseModel):
    hr_source: str = "none"  # apple_watch, ble, rppg, none


class SessionResponse(BaseModel):
    id: str
    status: str
    hr_source: str
    baseline_hr: float | None = None
    baseline_hrv: float | None = None
    truth_score: float | None = None
    created_at: str

    model_config = {"from_attributes": True}


@router.post("", response_model=SessionResponse)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    session = Session(hr_source=body.hr_source)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionResponse(
        id=session.id,
        status=session.status.value if isinstance(session.status, SessionStatus) else session.status,
        hr_source=session.hr_source,
        baseline_hr=session.baseline_hr,
        baseline_hrv=session.baseline_hrv,
        truth_score=session.truth_score,
        created_at=session.created_at.isoformat(),
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(
        id=session.id,
        status=session.status.value if isinstance(session.status, SessionStatus) else session.status,
        hr_source=session.hr_source,
        baseline_hr=session.baseline_hr,
        baseline_hrv=session.baseline_hrv,
        truth_score=session.truth_score,
        created_at=session.created_at.isoformat(),
    )


@router.get("", response_model=list[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).order_by(Session.created_at.desc()))
    sessions = result.scalars().all()
    return [
        SessionResponse(
            id=s.id,
            status=s.status.value if isinstance(s.status, SessionStatus) else s.status,
            hr_source=s.hr_source,
            baseline_hr=s.baseline_hr,
            baseline_hrv=s.baseline_hrv,
            truth_score=s.truth_score,
            created_at=s.created_at.isoformat(),
        )
        for s in sessions
    ]
