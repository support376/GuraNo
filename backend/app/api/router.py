from fastapi import APIRouter

from app.api.sessions import router as sessions_router
from app.api.questions import router as questions_router
from app.api.reports import router as reports_router
from app.api.ws import router as ws_router

api_router = APIRouter()

api_router.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])
api_router.include_router(questions_router, prefix="/api/questions", tags=["questions"])
api_router.include_router(reports_router, prefix="/api/reports", tags=["reports"])
api_router.include_router(ws_router, tags=["websocket"])
