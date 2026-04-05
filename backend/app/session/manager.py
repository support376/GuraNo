import asyncio
import json
import logging
import time
from collections import deque
from datetime import datetime

import numpy as np
from fastapi import WebSocket

from app.config import settings
from app.analysis.voice.analyzer import VoiceAnalyzer
from app.analysis.face.analyzer import FaceAnalyzer
from app.analysis.heartrate.analyzer import HRAnalyzer
from app.analysis.fusion.engine import FusionEngine
from app.detection.detector import LieDetector
from app.session.question_flow import QuestionFlow

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, session_id: str, websocket: WebSocket):
        self.session_id = session_id
        self.ws = websocket
        self.is_running = False
        self.is_calibrating = False

        # Analyzers
        self.voice_analyzer = VoiceAnalyzer()
        self.face_analyzer = FaceAnalyzer()
        self.hr_analyzer = HRAnalyzer()
        self.fusion_engine = FusionEngine()
        self.lie_detector = LieDetector(session_id)
        self.question_flow: QuestionFlow | None = None

        # Buffers
        self.audio_buffer = bytearray()
        self.frame_buffer: deque = deque(maxlen=300)
        self.hr_buffer: deque = deque(maxlen=120)

        # Timing
        self.last_analysis_time = 0.0
        self.analysis_interval = settings.analysis_interval_sec

        # Current state
        self.current_hr = 0.0

    async def initialize(self):
        try:
            await self.voice_analyzer.initialize()
        except Exception as e:
            logger.warning(f"Voice analyzer init failed: {e}")
        try:
            await self.face_analyzer.initialize()
        except Exception as e:
            logger.warning(f"Face analyzer init failed: {e}")
        logger.info(f"Session {self.session_id} initialized")

    async def send(self, msg: dict):
        try:
            await self.ws.send_text(json.dumps(msg, ensure_ascii=False))
        except Exception as e:
            logger.error(f"WS send error: {e}")

    async def start_calibration(self):
        self.is_calibrating = True
        self.hr_analyzer.start_baseline_collection()
        self.voice_analyzer.start_baseline_collection()
        await self.send({"type": "status", "message": "기준선 수립을 시작합니다."})

    async def finish_calibration(self):
        self.is_calibrating = False
        self.hr_analyzer.finalize_baseline()
        self.voice_analyzer.finalize_baseline()
        await self.send({
            "type": "baseline_ready",
            "baseline_hr": self.hr_analyzer.baseline_hr,
            "baseline_hrv": self.hr_analyzer.baseline_hrv,
            "baseline_pitch": self.voice_analyzer.baseline_pitch,
        })

    async def start_session(self):
        self.is_running = True
        self.question_flow = QuestionFlow(self.session_id, self.ws)
        await self.question_flow.load_questions()
        await self.send({"type": "status", "message": "테스트를 시작합니다."})
        await self.question_flow.ask_current()

    async def stop_session(self):
        self.is_running = False
        try:
            report_data = await self.lie_detector.generate_report()
            await self.send({"type": "session_complete", "report": report_data})
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            await self.send({"type": "session_complete", "report": {"error": str(e)}})

    async def next_question(self):
        if self.question_flow:
            has_next = await self.question_flow.advance()
            if not has_next:
                await self.stop_session()

    async def handle_video_frame(self, frame_data: bytes, ts: float):
        self.frame_buffer.append((frame_data, ts))

        now = time.time()
        if now - self.last_analysis_time >= self.analysis_interval:
            self.last_analysis_time = now
            await self._run_analysis(ts)

    async def handle_audio_chunk(self, audio_data: bytes, ts: float):
        self.audio_buffer.extend(audio_data)
        if len(self.audio_buffer) >= 64000:
            audio_segment = bytes(self.audio_buffer)
            self.audio_buffer.clear()
            try:
                await self.voice_analyzer.process_chunk(audio_segment, ts)
            except Exception as e:
                logger.warning(f"Voice processing error: {e}")

    async def handle_heart_rate(self, bpm: float, source: str, ts: float):
        self.current_hr = bpm
        self.hr_buffer.append((bpm, ts))
        self.hr_analyzer.add_reading(bpm, ts)
        if self.is_calibrating:
            self.hr_analyzer.add_baseline_reading(bpm)

    async def _run_analysis(self, ts: float):
        """Run all analyzers - each one is independent, failures don't block others."""
        if not self.frame_buffer:
            return

        frame_data, frame_ts = self.frame_buffer[-1]

        # Voice (never crashes the pipeline)
        try:
            voice_result = self.voice_analyzer.get_current_scores()
        except Exception as e:
            logger.warning(f"Voice analysis error: {e}")
            voice_result = {"lie_probability": 0.0}

        # Face (never crashes the pipeline)
        try:
            face_result = await self.face_analyzer.analyze_frame(frame_data)
        except Exception as e:
            logger.warning(f"Face analysis error: {e}")
            face_result = {"lie_probability": 0.0}

        # HR (never crashes the pipeline)
        try:
            hr_result = self.hr_analyzer.get_current_scores()
        except Exception as e:
            logger.warning(f"HR analysis error: {e}")
            hr_result = {"lie_probability": 0.0}

        # Fusion
        try:
            fusion_result = self.fusion_engine.fuse(
                voice_score=voice_result.get("lie_probability", 0),
                face_score=face_result.get("lie_probability", 0),
                hr_score=hr_result.get("lie_probability", 0),
            )
        except Exception:
            fusion_result = {"fusion_score": 0.0}

        verdict = self._get_verdict(fusion_result.get("fusion_score", 0))

        # Always send result to frontend
        await self.send({
            "type": "analysis_result",
            "ts": ts,
            "voice_score": voice_result.get("lie_probability", 0),
            "face_score": face_result.get("lie_probability", 0),
            "hr_score": hr_result.get("lie_probability", 0),
            "fusion_score": fusion_result.get("fusion_score", 0),
            "verdict": verdict,
            "current_hr": self.current_hr,
            "baseline_hr": self.hr_analyzer.baseline_hr,
            "transcript": self.voice_analyzer.latest_transcript,
        })

        # Lie detection
        if verdict == "거짓" and self.is_running:
            try:
                await self.lie_detector.on_lie_detected(
                    frame_data=frame_data,
                    frame_buffer=list(self.frame_buffer),
                    fusion_score=fusion_result.get("fusion_score", 0),
                    voice_result=voice_result,
                    face_result=face_result,
                    hr_result=hr_result,
                    transcript=self.voice_analyzer.latest_transcript,
                    question=self.question_flow.current_question_text if self.question_flow else "",
                    question_id=self.question_flow.current_question_id if self.question_flow else "",
                    ts=ts,
                    ws=self.ws,
                )
            except Exception as e:
                logger.warning(f"Lie detection event error: {e}")

        # Record
        if self.is_running and self.question_flow:
            try:
                self.lie_detector.record_analysis(
                    question_id=self.question_flow.current_question_id,
                    voice_result=voice_result,
                    face_result=face_result,
                    hr_result=hr_result,
                    fusion_result=fusion_result,
                    verdict=verdict,
                    transcript=self.voice_analyzer.latest_transcript,
                    hr_bpm=self.current_hr,
                )
            except Exception as e:
                logger.warning(f"Record analysis error: {e}")

    def _get_verdict(self, fusion_score: float) -> str:
        if fusion_score >= settings.lie_threshold:
            return "거짓"
        elif fusion_score >= settings.suspect_threshold:
            return "의심"
        return "진실"

    async def cleanup(self):
        self.is_running = False
        logger.info(f"Session {self.session_id} cleaned up")
