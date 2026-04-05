"""Seed sample questions for testing."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.db.database import async_session, init_db
from app.models.session import Session
from app.models.question import Question


SAMPLE_QUESTIONS = [
    {"text": "어제 몇 시에 퇴근했나요?", "category": "sensitive"},
    {"text": "지난주 회의에서 보고한 수치가 정확한가요?", "category": "sensitive"},
    {"text": "이 프로젝트의 진행 상황을 솔직하게 말씀해주세요.", "category": "sensitive"},
    {"text": "팀원들과의 관계에서 갈등이 있나요?", "category": "sensitive"},
    {"text": "최근에 회사 규정을 어긴 적이 있나요?", "category": "sensitive"},
    {"text": "업무 시간에 개인 용무를 본 적이 있나요?", "category": "sensitive"},
]


async def seed():
    await init_db()
    async with async_session() as db:
        session = Session(hr_source="rppg")
        db.add(session)
        await db.flush()

        for i, q in enumerate(SAMPLE_QUESTIONS):
            question = Question(
                session_id=session.id,
                order=i + 1,
                text=q["text"],
                category=q["category"],
            )
            db.add(question)

        await db.commit()
        print(f"Created session: {session.id}")
        print(f"Added {len(SAMPLE_QUESTIONS)} questions")


if __name__ == "__main__":
    asyncio.run(seed())
