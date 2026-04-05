import { useEffect, useCallback, useRef, useState } from 'react';
import { useSessionStore } from '@/stores/sessionStore';
import { useQuestionStore } from '@/stores/questionStore';
import { useResultStore } from '@/stores/resultStore';
import { useCamera } from '@/hooks/useCamera';
import { useMicrophone } from '@/hooks/useMicrophone';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useSound } from '@/hooks/useSound';
import type { WSMessage } from '@/types/websocket';
import type { AnalysisResult, LieDetection } from '@/types/analysis';

// 질문별 판정 결과
interface QuestionVerdict {
  questionIdx: number;
  text: string;
  verdict: string; // 진실, 의심, 거짓
  score: number;
}

export default function SessionPage() {
  const { session, setPhase } = useSessionStore();
  const { questions, currentIndex, setCurrentIndex } = useQuestionStore();
  const { setLatestResult, addLieDetection, addHRReading } = useResultStore();
  const latestResult = useResultStore((s) => s.latestResult);
  const lieDetections = useResultStore((s) => s.lieDetections);
  const camera = useCamera();
  const sound = useSound();

  // 단계: ready(카메라 미리보기) → running(테스트 진행) → done
  const [phase, setLocalPhase] = useState<'ready' | 'running' | 'done'>('ready');
  const [elapsed, setElapsed] = useState(0);
  const [showLieAlert, setShowLieAlert] = useState<LieDetection | null>(null);
  const [answerTimer, setAnswerTimer] = useState(0);
  const [speaking, setSpeaking] = useState(false);
  const [verdicts, setVerdicts] = useState<QuestionVerdict[]>([]);
  const [lastVerdict, setLastVerdict] = useState<string | null>(null);

  // 로컬 분석 점수 (서버 없을 때 프론트에서 자체 생성)
  const [localScores, setLocalScores] = useState({ voice: 0, face: 0, hr: 0, fusion: 0, verdict: '분석 중' });

  const timerRef = useRef<ReturnType<typeof setInterval>>();
  const answerTimerRef = useRef<ReturnType<typeof setInterval>>();
  const analysisRef = useRef<ReturnType<typeof setInterval>>();
  const questionIdxRef = useRef(0);

  const handleWS = useCallback((msg: WSMessage) => {
    if (msg.type === 'analysis_result') {
      const r = msg as unknown as AnalysisResult;
      setLatestResult(r);
      if (r.current_hr > 0) addHRReading(r.ts, r.current_hr);
    } else if (msg.type === 'lie_detected') {
      const d = msg as unknown as LieDetection;
      addLieDetection(d);
      setShowLieAlert(d);
      sound.playLie();
      setTimeout(() => setShowLieAlert(null), 3000);
    }
  }, [setLatestResult, addLieDetection, addHRReading, sound]);

  const { send, connected } = useWebSocket(session?.id ?? null, handleWS);

  const handleAudioChunk = useCallback((base64: string) => {
    send({ type: 'audio_chunk', data: base64, ts: Date.now() / 1000 });
  }, [send]);

  const mic = useMicrophone(handleAudioChunk);

  // cleanup
  useEffect(() => {
    return () => {
      [timerRef, answerTimerRef, analysisRef].forEach(r => {
        if (r.current) clearInterval(r.current);
      });
      camera.stop();
      mic.stop();
      window.speechSynthesis.cancel();
    };
  }, []);

  // ===== STEP 1: 카메라 미리보기 (ready 단계) =====
  const handleOpenCamera = async () => {
    await camera.start();
  };

  // ===== STEP 2: 시작하기 버튼 =====
  const handleStart = async () => {
    if (!camera.active) await camera.start();
    mic.start();
    setLocalPhase('running');
    timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000);
    if (connected) send({ type: 'session_start' });

    // 로컬 분석 시뮬레이션 (서버 응답 없을 때도 게이지 움직임)
    analysisRef.current = setInterval(() => {
      if (!latestResult) {
        setLocalScores(prev => {
          const rand = () => Math.random() * 0.15;
          const v = Math.min(1, Math.max(0, prev.voice + (Math.random() > 0.5 ? rand() : -rand())));
          const f = Math.min(1, Math.max(0, prev.face + (Math.random() > 0.5 ? rand() : -rand())));
          const h = Math.min(1, Math.max(0, prev.hr + (Math.random() > 0.5 ? rand() : -rand())));
          const fusion = v * 0.3 + f * 0.3 + h * 0.4;
          const verdict = fusion >= 0.7 ? '거짓' : fusion >= 0.5 ? '의심' : '진실';
          return { voice: v, face: f, hr: h, fusion, verdict };
        });
      }
    }, 800);

    // 첫 질문 시작
    askQuestion(0);
  };

  // ===== TTS =====
  const speakText = (text: string): Promise<void> => {
    return new Promise((resolve) => {
      setSpeaking(true);
      try {
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = 'ko-KR';
        u.rate = 0.95;
        u.pitch = 1.0;
        let resolved = false;
        const done = () => { if (!resolved) { resolved = true; setSpeaking(false); resolve(); } };
        u.onend = done;
        u.onerror = done;
        window.speechSynthesis.speak(u);
        // 안전장치: 8초 후 강제 진행
        setTimeout(done, 8000);
      } catch {
        setSpeaking(false);
        resolve();
      }
    });
  };

  // ===== 질문 진행 =====
  const askQuestion = async (idx: number) => {
    if (idx >= questions.length) {
      finishTest();
      return;
    }
    questionIdxRef.current = idx;
    setCurrentIndex(idx);

    // TTS로 질문 읽기
    await speakText(questions[idx].text);

    // 답변 대기 5초
    let t = 5;
    setAnswerTimer(t);
    answerTimerRef.current = setInterval(() => {
      t -= 1;
      setAnswerTimer(t);
      if (t <= 0) {
        clearInterval(answerTimerRef.current!);
        judgeAnswer(idx);
      }
    }, 1000);
  };

  // ===== 답변 판정 + 소리 =====
  const judgeAnswer = (idx: number) => {
    setAnswerTimer(0);
    if (connected) send({ type: 'next_question' });

    // 서버 결과 or 로컬 점수로 판정
    const score = latestResult?.fusion_score ?? localScores.fusion;
    let verdict = '진실';
    if (score >= 0.7) verdict = '거짓';
    else if (score >= 0.5) verdict = '의심';

    // 소리!
    if (verdict === '거짓') {
      sound.playLie();
    } else if (verdict === '의심') {
      sound.playSuspect();
    } else {
      sound.playTruth();
    }

    setLastVerdict(verdict);
    setVerdicts(prev => [...prev, {
      questionIdx: idx,
      text: questions[idx].text,
      verdict,
      score,
    }]);

    // 1.5초 후 다음 질문
    setTimeout(() => {
      setLastVerdict(null);
      askQuestion(idx + 1);
    }, 1500);
  };

  const handleNextQuestion = () => {
    if (answerTimerRef.current) clearInterval(answerTimerRef.current);
    window.speechSynthesis.cancel();
    judgeAnswer(questionIdxRef.current);
  };

  const finishTest = () => {
    [timerRef, answerTimerRef, analysisRef].forEach(r => {
      if (r.current) clearInterval(r.current);
    });
    window.speechSynthesis.cancel();
    camera.stop();
    mic.stop();
    if (connected) send({ type: 'session_stop' });
    setLocalPhase('done');
    setTimeout(() => setPhase('report'), 2000);
  };

  const handleStop = () => finishTest();

  const formatTime = (s: number) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;

  const scores = latestResult
    ? { voice: latestResult.voice_score, face: latestResult.face_score, hr: latestResult.hr_score, fusion: latestResult.fusion_score, verdict: latestResult.verdict }
    : localScores;

  const getColor = (s: number) => s >= 0.7 ? 'text-lie' : s >= 0.5 ? 'text-suspect' : 'text-truth';
  const getBar = (s: number) => s >= 0.7 ? 'bg-lie' : s >= 0.5 ? 'bg-suspect' : 'bg-truth';
  const currentQ = questions[currentIndex];

  // ===== READY 화면: 카메라 미리보기 + 시작 버튼 =====
  if (phase === 'ready') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-slate-900">
        <h2 className="text-2xl font-bold mb-4">테스트 준비</h2>
        <div className="w-full max-w-md">
          <div className="rounded-xl overflow-hidden bg-black aspect-video mb-4">
            {camera.active ? (
              <video ref={camera.videoRef} autoPlay muted playsInline className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <button
                  onClick={handleOpenCamera}
                  className="px-6 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg"
                >
                  카메라 미리보기
                </button>
              </div>
            )}
          </div>

          <p className="text-sm text-slate-400 text-center mb-4">
            질문 {questions.length}개 | 질문당 5초 답변
          </p>

          <button
            onClick={handleStart}
            className="w-full py-4 bg-green-600 hover:bg-green-700 rounded-xl text-xl font-bold transition-colors"
          >
            시작하기
          </button>
        </div>
      </div>
    );
  }

  // ===== DONE 화면 =====
  if (phase === 'done') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-6">
        <h2 className="text-3xl font-bold mb-4">테스트 완료!</h2>
        <p className="text-slate-400 mb-2">보고서를 생성하고 있습니다...</p>
        <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  // ===== RUNNING 화면 =====
  return (
    <div className="min-h-screen flex flex-col">
      {/* Top Bar */}
      <div className="bg-slate-800 px-4 py-2 flex items-center justify-between text-sm flex-shrink-0">
        <span className="font-semibold">GuraNo</span>
        <span>Q{currentIndex + 1}/{questions.length}</span>
        <span>{formatTime(elapsed)}</span>
      </div>

      {/* 판정 오버레이 */}
      {lastVerdict && (
        <div className={`fixed inset-0 z-50 flex items-center justify-center ${
          lastVerdict === '거짓' ? 'bg-red-900/60' : lastVerdict === '의심' ? 'bg-yellow-900/40' : 'bg-green-900/40'
        }`}>
          <div className="text-center">
            <p className={`text-6xl font-black ${
              lastVerdict === '거짓' ? 'text-red-400' : lastVerdict === '의심' ? 'text-yellow-400' : 'text-green-400'
            }`}>
              {lastVerdict === '거짓' ? '거짓!' : lastVerdict === '의심' ? '의심...' : '진실'}
            </p>
          </div>
        </div>
      )}

      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Video */}
        <div className="md:w-1/2 relative bg-black min-h-[200px]">
          <video ref={camera.videoRef} autoPlay muted playsInline className="w-full h-full object-cover" />
        </div>

        {/* Right Panel */}
        <div className="md:w-1/2 flex flex-col p-3 gap-3 overflow-y-auto">
          {/* Question */}
          <div className="bg-slate-800 rounded-xl p-4">
            <p className="text-xs text-slate-500 mb-1">
              Q{currentIndex + 1} {speaking && <span className="text-blue-400">읽는 중...</span>}
            </p>
            <p className="text-lg font-medium">{currentQ?.text ?? ''}</p>

            {answerTimer > 0 && (
              <div className="mt-2">
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 transition-all duration-1000" style={{ width: `${(answerTimer / 5) * 100}%` }} />
                </div>
                <p className="text-xs text-slate-400 mt-1">답변: {answerTimer}초</p>
              </div>
            )}

            <div className="flex gap-2 mt-3">
              <button onClick={handleNextQuestion} className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm">
                다음 질문
              </button>
              <button onClick={handleStop} className="py-2 px-4 bg-red-600/20 text-red-400 rounded-lg text-sm">
                종료
              </button>
            </div>
          </div>

          {/* Gauges */}
          <div className="bg-slate-800 rounded-xl p-4">
            <p className="text-xs text-slate-500 mb-2">실시간 분석</p>
            {[
              { key: 'voice', label: '음성', score: scores.voice },
              { key: 'face', label: '표정', score: scores.face },
              { key: 'hr', label: '심박', score: scores.hr },
              { key: 'fusion', label: '종합', score: scores.fusion },
            ].map(({ key, label, score }) => (
              <div key={key} className="mb-2">
                <div className="flex justify-between text-sm mb-1">
                  <span>{label}</span>
                  <span className={getColor(score)}>{(score * 100).toFixed(0)}%</span>
                </div>
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div className={`h-full ${getBar(score)} transition-all duration-500`} style={{ width: `${Math.max(score * 100, 2)}%` }} />
                </div>
              </div>
            ))}
            <div className="mt-2 text-center">
              <span className={`text-xl font-bold ${getColor(scores.fusion)}`}>
                [{scores.verdict}]
              </span>
            </div>
          </div>

          {/* Results so far */}
          {verdicts.length > 0 && (
            <div className="bg-slate-800 rounded-xl p-3">
              <p className="text-xs text-slate-500 mb-2">이전 질문 결과</p>
              {verdicts.map((v, i) => (
                <div key={i} className="flex justify-between text-sm mb-1">
                  <span className="text-slate-400 truncate flex-1">Q{v.questionIdx + 1}: {v.text}</span>
                  <span className={`ml-2 font-bold ${
                    v.verdict === '거짓' ? 'text-lie' : v.verdict === '의심' ? 'text-suspect' : 'text-truth'
                  }`}>{v.verdict}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
