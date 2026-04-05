import asyncio
import json
import base64
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.session.manager import SessionManager

router = APIRouter()
logger = logging.getLogger(__name__)

# Active sessions: session_id -> SessionManager
active_sessions: dict[str, SessionManager] = {}


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected: session={session_id}")

    manager = SessionManager(session_id, websocket)
    active_sessions[session_id] = manager

    try:
        await manager.initialize()

        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "video_frame":
                frame_data = base64.b64decode(msg["data"])
                ts = msg.get("ts", datetime.utcnow().timestamp())
                await manager.handle_video_frame(frame_data, ts)

            elif msg_type == "audio_chunk":
                audio_data = base64.b64decode(msg["data"])
                ts = msg.get("ts", datetime.utcnow().timestamp())
                await manager.handle_audio_chunk(audio_data, ts)

            elif msg_type == "heart_rate":
                bpm = msg["bpm"]
                source = msg.get("source", "unknown")
                ts = msg.get("ts", datetime.utcnow().timestamp())
                await manager.handle_heart_rate(bpm, source, ts)

            elif msg_type == "session_start":
                await manager.start_session()

            elif msg_type == "session_stop":
                await manager.stop_session()

            elif msg_type == "calibration_start":
                await manager.start_calibration()

            elif msg_type == "calibration_done":
                await manager.finish_calibration()

            elif msg_type == "next_question":
                await manager.next_question()

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: session={session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_sessions.pop(session_id, None)
        await manager.cleanup()
