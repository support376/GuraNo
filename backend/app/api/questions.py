from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.database import get_db
from app.models.question import Question

router = APIRouter()


class QuestionCreate(BaseModel):
    session_id: str
    text: str
    order: int
    category: str = "sensitive"


class QuestionItem(BaseModel):
    text: str
    category: str = "sensitive"


class QuestionBulkCreate(BaseModel):
    session_id: str
    questions: list[QuestionItem]


class QuestionResponse(BaseModel):
    id: str
    session_id: str
    order: int
    text: str
    category: str

    model_config = {"from_attributes": True}


@router.post("", response_model=QuestionResponse)
async def create_question(body: QuestionCreate, db: AsyncSession = Depends(get_db)):
    q = Question(session_id=body.session_id, text=body.text, order=body.order, category=body.category)
    db.add(q)
    await db.commit()
    await db.refresh(q)
    return q


@router.post("/bulk", response_model=list[QuestionResponse])
async def create_questions_bulk(body: QuestionBulkCreate, db: AsyncSession = Depends(get_db)):
    questions = []
    for i, qdata in enumerate(body.questions):
        q = Question(
            session_id=body.session_id,
            text=qdata.text,
            order=i + 1,
            category=qdata.category,
        )
        db.add(q)
        questions.append(q)
    await db.commit()
    for q in questions:
        await db.refresh(q)
    return questions


@router.get("/session/{session_id}", response_model=list[QuestionResponse])
async def get_questions_by_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Question).where(Question.session_id == session_id).order_by(Question.order)
    )
    return result.scalars().all()


@router.delete("/{question_id}")
async def delete_question(question_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Question).where(Question.id == question_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    await db.delete(q)
    await db.commit()
    return {"ok": True}
