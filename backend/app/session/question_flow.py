import json
import logging
from fastapi import WebSocket
from sqlalchemy import select

from app.db.database import async_session
from app.models.question import Question

logger = logging.getLogger(__name__)


class QuestionFlow:
    def __init__(self, session_id: str, ws: WebSocket):
        self.session_id = session_id
        self.ws = ws
        self.questions: list[dict] = []
        self.current_index = 0

    @property
    def current_question_text(self) -> str:
        if 0 <= self.current_index < len(self.questions):
            return self.questions[self.current_index]["text"]
        return ""

    @property
    def current_question_id(self) -> str:
        if 0 <= self.current_index < len(self.questions):
            return self.questions[self.current_index]["id"]
        return ""

    async def load_questions(self):
        async with async_session() as db:
            result = await db.execute(
                select(Question)
                .where(Question.session_id == self.session_id)
                .order_by(Question.order)
            )
            rows = result.scalars().all()
            self.questions = [
                {"id": q.id, "text": q.text, "category": q.category, "order": q.order}
                for q in rows
            ]
        logger.info(f"Loaded {len(self.questions)} questions for session {self.session_id}")

    async def ask_current(self):
        if self.current_index >= len(self.questions):
            return False

        q = self.questions[self.current_index]
        await self.ws.send_text(json.dumps({
            "type": "tts_play",
            "text": q["text"],
            "question_index": self.current_index,
            "total_questions": len(self.questions),
            "question_id": q["id"],
            "category": q["category"],
        }, ensure_ascii=False))
        return True

    async def advance(self) -> bool:
        self.current_index += 1
        if self.current_index >= len(self.questions):
            return False
        await self.ask_current()
        return True
