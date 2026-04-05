import { useEffect, useCallback, useRef, useState } from 'react';
import { useSessionStore } from '@/stores/sessionStore';
import { useQuestionStore } from '@/stores/questionStore';
import { useResultStore } from '@/stores/resultStore';
import { useCamera } from '@/hooks/useCamera';
import { useMicrophone } from '@/hooks/useMicrophone';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useTTS } from '@/hooks/useTTS';
import type { WSMessage } from '@/types/websocket';
import type { AnalysisResult, LieDetection } from '@/types/analysis';

export default function SessionPage() {
  const { session, setPhase } = useSessionStore();
  const { questions, currentIndex, setCurrentIndex } = useQuestionStore();
  const { setLatestResult, addLieDetection, addHRReading } = useResultStore();
  const latestResult = useResultStore((s) => s.latestResult);
  const lieDetections = useResultStore((s) => s.lieDetections);
  const camera = useCamera();
  const tts = useTTS();
  const [elapsed, setElapsed] = useState(0);
  const [showLieAlert, setShowLieAlert] = useState<LieDetection | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval>>();

  const handleWS = useCallback((msg: WSMessage) => {
    if (msg.type === 'analysis_result') {
      const r = msg as unknown as AnalysisResult;
      setLatestResult(r);
      if (r.current_hr > 0) {
        addHRReading(r.ts, r.current_hr);
      }
    } else if (msg.type === 'lie_detected') {
      const d = msg as unknown as LieDetection;
      addLieDetection(d);
      setShowLieAlert(d);
      setTimeout(() => setShowLieAlert(null), 4000);
    } else if (msg.type === 'tts_play') {
      const text = msg.text as string;
      const idx = msg.question_index as number;
      setCurrentIndex(idx);
      tts.speak(text, () => {
        // After TTS finishes, wait for answer
      });
    } else if (msg.type === 'session_complete') {
      setPhase('report');
    }
  }, [setLatestResult, addLieDetection, addHRReading, setCurrentIndex, tts, setPhase]);

  const { send, connected } = useWebSocket(session?.id ?? null, handleWS);

  const handleAudioChunk = useCallback((base64: string) => {
    send({ type: 'audio_chunk', data: base64, ts: Date.now() / 1000 });
  }, [send]);

  const mic = useMicrophone(handleAudioChunk);

  // Start everything
  useEffect(() => {
    if (connected) {
      camera.start();
      mic.start();
      send({ type: 'session_start' });
      timerRef.current = setInterval(() => setElapsed((e) => e + 1), 1000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [connected]);

  // Send video frames at 30fps
  useEffect(() => {
    if (!camera.active || !connected) return;
    const interval = setInterval(() => {
      const frame = camera.captureFrame();
      if (frame) {
        send({ type: 'video_frame', data: frame, ts: Date.now() / 1000 });
      }
    }, 33);
    return () => clearInterval(interval);
  }, [camera.active, connected, send, camera.captureFrame]);

  const handleNextQuestion = () => {
    send({ type: 'next_question' });
  };

  const handleStop = () => {
    send({ type: 'session_stop' });
  };

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.7) return 'text-lie';
    if (score >= 0.5) return 'text-suspect';
    return 'text-truth';
  };

  const getBarColor = (score: number) => {
    if (score >= 0.7) return 'bg-lie';
    if (score >= 0.5) return 'bg-suspect';
    return 'bg-truth';
  };

  const currentQ = questions[currentIndex];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top Bar */}
      <div className="bg-slate-800 px-4 py-2 flex items-center justify-between text-sm">
        <span className="font-semibold">GuraNo</span>
        <span>Q{currentIndex + 1}/{questions.length}</span>
        <span>{formatTime(elapsed)}</span>
        <span className="text-red-400">
          {latestResult ? `${latestResult.current_hr.toFixed(0)} BPM` : '-- BPM'}
        </span>
      </div>

      {/* Main Content - responsive */}
      <div className="flex-1 flex flex-col md:flex-row">
        {/* Video */}
        <div className="md:w-1/2 relative bg-black">
          <video ref={camera.videoRef} autoPlay muted playsInline className="w-full h-full object-cover" />
          {/* Lie Alert Overlay */}
          {showLieAlert && (
            <div className="absolute inset-0 bg-red-600/30 flex items-center justify-center animate-pulse">
              <div className="bg-red-900/90 rounded-xl p-4 text-center max-w-sm">
                <p className="text-2xl font-bold text-red-300 mb-2">거짓 감지!</p>
                <p className="text-sm">{showLieAlert.reasons[0]}</p>
              </div>
            </div>
          )}
        </div>

        {/* Right Panel */}
        <div className="md:w-1/2 flex flex-col p-4 gap-4">
          {/* Current Question */}
          <div className="bg-slate-800 rounded-xl p-4">
            <p className="text-xs text-slate-500 mb-1">현재 질문</p>
            <p className="text-lg font-medium">{currentQ?.text ?? '대기 중...'}</p>
            <div className="flex gap-2 mt-3">
              <button
                onClick={handleNextQuestion}
                className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm transition-colors"
              >
                다음 질문
              </button>
              <button
                onClick={handleStop}
                className="py-2 px-4 bg-red-600/20 text-red-400 hover:bg-red-600/30 rounded-lg text-sm transition-colors"
              >
                종료
              </button>
            </div>
          </div>

          {/* Real-time Gauges */}
          <div className="bg-slate-800 rounded-xl p-4">
            <p className="text-xs text-slate-500 mb-2">실시간 분석</p>
            {(['voice_score', 'face_score', 'hr_score', 'fusion_score'] as const).map((key) => {
              const labels: Record<string, string> = {
                voice_score: '음성',
                face_score: '표정',
                hr_score: '심박',
                fusion_score: '종합',
              };
              const score = latestResult ? (latestResult[key] as number) : 0;
              return (
                <div key={key} className="mb-2">
                  <div className="flex justify-between text-sm mb-1">
                    <span>{labels[key]}</span>
                    <span className={getScoreColor(score)}>{(score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${getBarColor(score)} transition-all duration-300`}
                      style={{ width: `${score * 100}%` }}
                    />
                  </div>
                </div>
              );
            })}
            {latestResult && (
              <div className="mt-2 text-center">
                <span className={`text-xl font-bold ${getScoreColor(latestResult.fusion_score)}`}>
                  [{latestResult.verdict}]
                </span>
              </div>
            )}
          </div>

          {/* HR */}
          <div className="bg-slate-800 rounded-xl p-4">
            <div className="flex justify-between items-center">
              <span className="text-xs text-slate-500">심박수</span>
              <span className="text-2xl font-bold text-red-400">
                {latestResult?.current_hr?.toFixed(0) ?? '--'} <span className="text-sm">BPM</span>
              </span>
            </div>
            {latestResult?.baseline_hr && (
              <p className="text-xs text-slate-500 mt-1">
                기준선: {latestResult.baseline_hr.toFixed(0)} BPM
                {latestResult.current_hr > 0 && (
                  <span className={latestResult.current_hr > latestResult.baseline_hr + 5 ? 'text-red-400' : 'text-green-400'}>
                    {' '}({latestResult.current_hr > latestResult.baseline_hr ? '+' : ''}{(latestResult.current_hr - latestResult.baseline_hr).toFixed(0)})
                  </span>
                )}
              </p>
            )}
          </div>

          {/* Lie Detections Log */}
          {lieDetections.length > 0 && (
            <div className="bg-slate-800 rounded-xl p-4 max-h-40 overflow-y-auto">
              <p className="text-xs text-slate-500 mb-2">거짓 감지 기록</p>
              {lieDetections.map((d, i) => (
                <div key={i} className="text-sm text-red-300 mb-1">
                  [{new Date(d.ts * 1000).toLocaleTimeString('ko-KR')}] {d.reasons[0]}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
