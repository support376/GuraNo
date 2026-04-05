import { useEffect, useCallback, useRef, useState } from 'react';
import { useSessionStore } from '@/stores/sessionStore';
import { useQuestionStore } from '@/stores/questionStore';
import { useResultStore } from '@/stores/resultStore';
import { useCamera } from '@/hooks/useCamera';
import { useAudioLevel } from '@/hooks/useAudioLevel';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useSound } from '@/hooks/useSound';
import type { WSMessage } from '@/types/websocket';
import type { AnalysisResult, LieDetection } from '@/types/analysis';

interface QuestionVerdict {
  questionIdx: number;
  text: string;
  verdict: string;
  score: number;
}

export default function SessionPage() {
  const { session, setPhase } = useSessionStore();
  const { questions, currentIndex, setCurrentIndex } = useQuestionStore();
  const { setLatestResult, addLieDetection, addHRReading } = useResultStore();
  const latestResult = useResultStore((s) => s.latestResult);
  const camera = useCamera();
  const audio = useAudioLevel();
  const sound = useSound();

  const [phase, setLocalPhase] = useState<'ready' | 'running' | 'done'>('ready');
  const [elapsed, setElapsed] = useState(0);
  const [answerTimer, setAnswerTimer] = useState(0);
  const [speaking, setSpeaking] = useState(false);
  const [verdicts, setVerdicts] = useState<QuestionVerdict[]>([]);
  const [lastVerdict, setLastVerdict] = useState<string | null>(null);
  const [voiceScore, setVoiceScore] = useState(0);
  const [faceScore, setFaceScore] = useState(0);
  const [hrScore, setHrScore] = useState(0);
  const [fusionScore, setFusionScore] = useState(0);
  const [verdictText, setVerdictText] = useState('대기');

  const timerRef = useRef<ReturnType<typeof setInterval>>();
  const answerTimerRef = useRef<ReturnType<typeof setInterval>>();
  const analysisRef = useRef<ReturnType<typeof setInterval>>();
  const questionIdxRef = useRef(0);
  const peakAudioRef = useRef(0); // 답변 중 최대 음량

  const handleWS = useCallback((msg: WSMessage) => {
    if (msg.type === 'analysis_result') {
      const r = msg as unknown as AnalysisResult;
      setLatestResult(r);
      setVoiceScore(r.voice_score);
      setFaceScore(r.face_score);
      setHrScore(r.hr_score);
      setFusionScore(r.fusion_score);
      setVerdictText(r.verdict);
    } else if (msg.type === 'lie_detected') {
      const d = msg as unknown as LieDetection;
      addLieDetection(d);
      sound.playLie();
    }
  }, [setLatestResult, addLieDetection, sound]);

  const { send, connected } = useWebSocket(session?.id ?? null, handleWS);

  // cleanup
  useEffect(() => {
    return () => {
      [timerRef, answerTimerRef, analysisRef].forEach(r => { if (r.current) clearInterval(r.current); });
      camera.stop();
      audio.stop();
      window.speechSynthesis.cancel();
    };
  }, []);

  // 실시간 로컬 분석: 마이크 음량 기반
  useEffect(() => {
    if (phase !== 'running') return;
    analysisRef.current = setInterval(() => {
      // 음성 점수: 마이크 음량 기반 (크게 말하면 높아짐)
      const vol = audio.level;
      const v = Math.min(1, vol * 5 + Math.random() * 0.1);
      setVoiceScore(prev => latestResult ? latestResult.voice_score : prev * 0.7 + v * 0.3);

      // 표정/심박: 부드럽게 변화
      setFaceScore(prev => latestResult ? latestResult.face_score : Math.min(1, Math.max(0, prev + (Math.random() - 0.5) * 0.08)));
      setHrScore(prev => latestResult ? latestResult.hr_score : Math.min(1, Math.max(0, prev + (Math.random() - 0.5) * 0.06)));

      // 종합
      setFusionScore(prev => {
        const f = voiceScore * 0.4 + faceScore * 0.3 + hrScore * 0.3;
        return latestResult ? latestResult.fusion_score : f;
      });

      const f = voiceScore * 0.4 + faceScore * 0.3 + hrScore * 0.3;
      setVerdictText(f >= 0.7 ? '거짓' : f >= 0.5 ? '의심' : '진실');

      // 답변 중 최대 음량 기록
      if (vol > peakAudioRef.current) peakAudioRef.current = vol;
    }, 500);
    return () => { if (analysisRef.current) clearInterval(analysisRef.current); };
  }, [phase, audio.level, latestResult]);

  // ===== READY: 카메라 열고 시작 =====
  const handleStart = async () => {
    await camera.start();
    await audio.start();
    setLocalPhase('running');
    timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000);
    if (connected) send({ type: 'session_start' });
    // 1초 후 첫 질문 시작
    setTimeout(() => askQuestion(0), 1000);
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
        let done = false;
        const finish = () => { if (!done) { done = true; setSpeaking(false); resolve(); } };
        u.onend = finish;
        u.onerror = finish;
        window.speechSynthesis.speak(u);
        setTimeout(finish, 8000);
      } catch {
        setSpeaking(false);
        resolve();
      }
    });
  };

  // ===== 질문 =====
  const askQuestion = async (idx: number) => {
    if (idx >= questions.length) { finishTest(); return; }
    questionIdxRef.current = idx;
    setCurrentIndex(idx);
    peakAudioRef.current = 0;

    await speakText(questions[idx].text);

    // 답변 대기 5초
    let t = 5;
    setAnswerTimer(t);
    answerTimerRef.current = setInterval(() => {
      t -= 1;
      setAnswerTimer(t);
      if (t <= 0) { clearInterval(answerTimerRef.current!); judgeAnswer(idx); }
    }, 1000);
  };

  // ===== 판정 + 소리 =====
  const judgeAnswer = (idx: number) => {
    setAnswerTimer(0);
    if (connected) send({ type: 'next_question' });

    // 판정: 서버 결과 or 음량 기반 로컬 판정
    const peak = peakAudioRef.current;
    const score = latestResult?.fusion_score ?? (voiceScore * 0.4 + faceScore * 0.3 + hrScore * 0.3);
    let verdict = '진실';
    if (score >= 0.65) verdict = '거짓';
    else if (score >= 0.45) verdict = '의심';

    if (verdict === '거짓') sound.playLie();
    else if (verdict === '의심') sound.playSuspect();
    else sound.playTruth();

    setLastVerdict(verdict);
    setVerdicts(prev => [...prev, { questionIdx: idx, text: questions[idx].text, verdict, score }]);

    setTimeout(() => { setLastVerdict(null); askQuestion(idx + 1); }, 1800);
  };

  const handleNextQuestion = () => {
    if (answerTimerRef.current) clearInterval(answerTimerRef.current);
    window.speechSynthesis.cancel();
    judgeAnswer(questionIdxRef.current);
  };

  const finishTest = () => {
    [timerRef, answerTimerRef, analysisRef].forEach(r => { if (r.current) clearInterval(r.current); });
    window.speechSynthesis.cancel();
    camera.stop();
    audio.stop();
    if (connected) send({ type: 'session_stop' });
    setLocalPhase('done');
    setTimeout(() => setPhase('report'), 2000);
  };

  const fmt = (s: number) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
  const clr = (s: number) => s >= 0.7 ? 'text-lie' : s >= 0.5 ? 'text-suspect' : 'text-truth';
  const bar = (s: number) => s >= 0.7 ? 'bg-lie' : s >= 0.5 ? 'bg-suspect' : 'bg-truth';

  // ===== READY =====
  if (phase === 'ready') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-6">
        <h2 className="text-2xl font-bold mb-2">테스트 준비</h2>
        <p className="text-slate-400 text-sm mb-6">질문 {questions.length}개 | 질문당 5초 답변</p>
        <div className="w-full max-w-md">
          {/* 비디오 항상 존재 */}
          <div className="rounded-xl overflow-hidden bg-black aspect-video mb-6">
            <video ref={camera.videoRef} autoPlay muted playsInline className="w-full h-full object-cover" />
          </div>
          {camera.error && <p className="text-red-400 text-sm mb-3 text-center">{camera.error}</p>}
          <button
            onClick={handleStart}
            className="w-full py-5 bg-green-600 hover:bg-green-700 rounded-xl text-2xl font-bold transition-colors"
          >
            시작하기
          </button>
        </div>
      </div>
    );
  }

  // ===== DONE =====
  if (phase === 'done') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-6">
        <h2 className="text-3xl font-bold mb-4">테스트 완료!</h2>
        <div className="space-y-2 w-full max-w-sm mb-6">
          {verdicts.map((v, i) => (
            <div key={i} className="flex justify-between bg-slate-800 rounded-lg p-3">
              <span className="text-sm text-slate-300 truncate flex-1">Q{i + 1}: {v.text}</span>
              <span className={`ml-2 font-bold ${v.verdict === '거짓' ? 'text-lie' : v.verdict === '의심' ? 'text-suspect' : 'text-truth'}`}>
                {v.verdict}
              </span>
            </div>
          ))}
        </div>
        <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
        <p className="text-slate-400 mt-2 text-sm">보고서 생성 중...</p>
      </div>
    );
  }

  // ===== RUNNING =====
  return (
    <div className="min-h-screen flex flex-col">
      {/* Top */}
      <div className="bg-slate-800 px-4 py-2 flex items-center justify-between text-sm">
        <span className="font-semibold">GuraNo</span>
        <span>Q{currentIndex + 1}/{questions.length}</span>
        <span>{fmt(elapsed)}</span>
      </div>

      {/* 판정 오버레이 */}
      {lastVerdict && (
        <div className={`fixed inset-0 z-50 flex items-center justify-center ${
          lastVerdict === '거짓' ? 'bg-red-900/70' : lastVerdict === '의심' ? 'bg-yellow-900/50' : 'bg-green-900/50'
        }`}>
          <p className={`text-7xl font-black ${
            lastVerdict === '거짓' ? 'text-red-400' : lastVerdict === '의심' ? 'text-yellow-400' : 'text-green-400'
          }`}>
            {lastVerdict === '거짓' ? '거짓!' : lastVerdict === '의심' ? '의심' : '진실!'}
          </p>
        </div>
      )}

      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Video - 항상 렌더 */}
        <div className="md:w-1/2 relative bg-black min-h-[200px]">
          <video ref={camera.videoRef} autoPlay muted playsInline className="w-full h-full object-cover" />
          {/* 마이크 레벨 표시 */}
          <div className="absolute bottom-2 left-2 right-2">
            <div className="h-1 bg-slate-700/50 rounded-full overflow-hidden">
              <div className="h-full bg-green-400 transition-all duration-100" style={{ width: `${Math.min(audio.level * 500, 100)}%` }} />
            </div>
          </div>
        </div>

        {/* Panel */}
        <div className="md:w-1/2 flex flex-col p-3 gap-3 overflow-y-auto">
          {/* Question */}
          <div className="bg-slate-800 rounded-xl p-4">
            <p className="text-xs text-slate-500 mb-1">
              Q{currentIndex + 1} {speaking && <span className="text-blue-400">읽는 중...</span>}
              {audio.isSpeaking && !speaking && <span className="text-green-400 ml-1">응답 감지</span>}
            </p>
            <p className="text-lg font-medium">{questions[currentIndex]?.text ?? ''}</p>

            {answerTimer > 0 && (
              <div className="mt-2">
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 transition-all duration-1000" style={{ width: `${(answerTimer / 5) * 100}%` }} />
                </div>
                <p className="text-xs text-slate-400 mt-1">답변: {answerTimer}초</p>
              </div>
            )}

            <div className="flex gap-2 mt-3">
              <button onClick={handleNextQuestion} className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm">다음 질문</button>
              <button onClick={finishTest} className="py-2 px-4 bg-red-600/20 text-red-400 rounded-lg text-sm">종료</button>
            </div>
          </div>

          {/* Gauges */}
          <div className="bg-slate-800 rounded-xl p-4">
            <p className="text-xs text-slate-500 mb-2">실시간 분석</p>
            {[
              { label: '음성', score: voiceScore },
              { label: '표정', score: faceScore },
              { label: '심박', score: hrScore },
              { label: '종합', score: fusionScore },
            ].map(({ label, score }) => (
              <div key={label} className="mb-2">
                <div className="flex justify-between text-sm mb-1">
                  <span>{label}</span>
                  <span className={clr(score)}>{(score * 100).toFixed(0)}%</span>
                </div>
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div className={`h-full ${bar(score)} transition-all duration-500`} style={{ width: `${Math.max(score * 100, 2)}%` }} />
                </div>
              </div>
            ))}
            <div className="mt-2 text-center">
              <span className={`text-xl font-bold ${clr(fusionScore)}`}>[{verdictText}]</span>
            </div>
          </div>

          {/* Previous */}
          {verdicts.length > 0 && (
            <div className="bg-slate-800 rounded-xl p-3">
              <p className="text-xs text-slate-500 mb-2">이전 결과</p>
              {verdicts.map((v, i) => (
                <div key={i} className="flex justify-between text-sm mb-1">
                  <span className="text-slate-400 truncate flex-1">Q{v.questionIdx + 1}</span>
                  <span className={`ml-2 font-bold ${v.verdict === '거짓' ? 'text-lie' : v.verdict === '의심' ? 'text-suspect' : 'text-truth'}`}>{v.verdict}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
