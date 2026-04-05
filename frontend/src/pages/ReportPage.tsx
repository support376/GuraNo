import { useEffect, useState, useRef } from 'react';
import { useSessionStore } from '@/stores/sessionStore';
import { useResultStore } from '@/stores/resultStore';
import { useQuestionStore } from '@/stores/questionStore';
import { reportApi } from '@/services/api';
import type { ReportData } from '@/types/analysis';

export default function ReportPage() {
  const { session, setPhase } = useSessionStore();
  const storeReport = useResultStore((s) => s.report);
  const setReport = useResultStore((s) => s.setReport);
  const hrHistory = useResultStore((s) => s.hrHistory);
  const lieDetections = useResultStore((s) => s.lieDetections);
  const questions = useQuestionStore((s) => s.questions);
  const [report, setLocalReport] = useState<ReportData | null>(storeReport);
  const [loading, setLoading] = useState(true);
  const [retries, setRetries] = useState(0);
  const retryRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    if (storeReport) {
      setLocalReport(storeReport);
      setLoading(false);
      return;
    }
    if (!session) {
      setLoading(false);
      return;
    }

    const fetchReport = () => {
      reportApi.get(session.id).then((r) => {
        setReport(r);
        setLocalReport(r);
        setLoading(false);
      }).catch(() => {
        if (retries < 3) {
          retryRef.current = setTimeout(() => {
            setRetries((r) => r + 1);
            fetchReport();
          }, 2000);
        } else {
          setLoading(false);
        }
      });
    };

    fetchReport();
    return () => { if (retryRef.current) clearTimeout(retryRef.current); };
  }, [session, storeReport, setReport, retries]);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mb-4" />
        <p className="text-slate-400">보고서 생성 중... ({retries}/3)</p>
      </div>
    );
  }

  // 서버 보고서가 없으면 로컬 데이터로 기본 보고서 생성
  const displayReport = report || buildLocalReport();

  function buildLocalReport(): ReportData {
    return {
      id: 'local',
      session_id: session?.id || '',
      truth_score: 50,
      total_questions: questions.length,
      lie_count: lieDetections.length,
      suspect_count: 0,
      truth_count: Math.max(0, questions.length - lieDetections.length),
      hr_peak_bpm: hrHistory.length > 0 ? Math.max(...hrHistory.map(h => h.bpm)) : null,
      hr_peak_question: null,
      hr_lowest_bpm: hrHistory.length > 0 ? Math.min(...hrHistory.map(h => h.bpm)) : null,
      hr_lowest_question: null,
      modality_weights: { voice: 0.30, face: 0.30, hr: 0.40 },
      hr_timeline: hrHistory.length > 0 ? {
        timestamps: hrHistory.map(h => h.ts),
        bpm: hrHistory.map(h => h.bpm),
        questions: [],
      } : null,
      pdf_path: null,
      answers: questions.map((q, i) => ({
        question_id: q.id,
        transcript: null,
        voice_score: null,
        face_score: null,
        hr_score: null,
        fusion_score: null,
        verdict: '분석 중',
        hr_bpm: null,
        reasons: null,
        screenshot_path: null,
      })),
    };
  }

  const getVerdictStyle = (verdict: string | null) => {
    if (verdict === '거짓') return 'text-lie bg-lie/10 border-lie/30';
    if (verdict === '의심') return 'text-suspect bg-suspect/10 border-suspect/30';
    if (verdict === '진실') return 'text-truth bg-truth/10 border-truth/30';
    return 'text-slate-400 bg-slate-800 border-slate-700';
  };

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold mb-1">GuraNo 분석 보고서</h2>
      <p className="text-sm text-slate-500 mb-6">
        {session?.created_at ? new Date(session.created_at).toLocaleString('ko-KR') : ''}
        {!report && <span className="text-yellow-500 ml-2">(로컬 데이터)</span>}
      </p>

      {/* Truth Score */}
      <div className="bg-slate-800 rounded-xl p-6 mb-6 text-center">
        <p className="text-sm text-slate-400 mb-2">종합 진실성 점수</p>
        <p className={`text-5xl font-bold ${
          displayReport.truth_score >= 70 ? 'text-truth' : displayReport.truth_score >= 50 ? 'text-suspect' : 'text-lie'
        }`}>
          {displayReport.truth_score.toFixed(0)}%
        </p>
        <div className="h-3 bg-slate-700 rounded-full overflow-hidden mt-4 max-w-xs mx-auto">
          <div
            className={`h-full rounded-full ${
              displayReport.truth_score >= 70 ? 'bg-truth' : displayReport.truth_score >= 50 ? 'bg-suspect' : 'bg-lie'
            }`}
            style={{ width: `${displayReport.truth_score}%` }}
          />
        </div>
        <p className="text-sm text-slate-400 mt-2">
          {displayReport.total_questions}개 답변 중 {displayReport.lie_count}개 거짓, {displayReport.suspect_count}개 의심
        </p>
      </div>

      {/* HR Summary */}
      {(displayReport.hr_peak_bpm || hrHistory.length > 0) && (
        <div className="bg-slate-800 rounded-xl p-4 mb-6">
          <h3 className="text-sm text-slate-400 mb-3">심박수 요약</h3>
          <div className="flex justify-around text-center">
            <div>
              <p className="text-2xl font-bold text-red-400">
                {displayReport.hr_peak_bpm?.toFixed(0) ?? '--'}
              </p>
              <p className="text-xs text-slate-500">최고 BPM</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-400">
                {displayReport.hr_lowest_bpm?.toFixed(0) ?? '--'}
              </p>
              <p className="text-xs text-slate-500">최저 BPM</p>
            </div>
          </div>
        </div>
      )}

      {/* Question Results */}
      <div className="space-y-3 mb-6">
        <h3 className="text-sm text-slate-400">질문별 상세</h3>
        {displayReport.answers.map((a, i) => (
          <div key={i} className={`border rounded-xl p-4 ${getVerdictStyle(a.verdict)}`}>
            <div className="flex justify-between items-start mb-2">
              <div>
                <span className="text-xs text-slate-400">Q{i + 1}</span>
                <p className="text-sm font-medium">{questions[i]?.text ?? ''}</p>
              </div>
              <span className="text-sm font-semibold">
                {a.verdict ?? '분석 중'}
                {a.fusion_score != null && ` (${(a.fusion_score * 100).toFixed(0)}%)`}
              </span>
            </div>
            {a.transcript && <p className="text-sm mb-2">A: "{a.transcript}"</p>}
            {a.hr_bpm != null && (
              <p className="text-xs text-slate-400">심박수: {a.hr_bpm.toFixed(0)} BPM</p>
            )}
          </div>
        ))}
      </div>

      {/* Lie Detections */}
      {lieDetections.length > 0 && (
        <div className="bg-slate-800 rounded-xl p-4 mb-6">
          <h3 className="text-sm text-slate-400 mb-3">거짓 감지 기록</h3>
          {lieDetections.map((d, i) => (
            <div key={i} className="text-sm text-red-300 mb-2 border-b border-slate-700 pb-2">
              <p className="font-medium">[{new Date(d.ts * 1000).toLocaleTimeString('ko-KR')}]</p>
              {d.reasons.map((r, j) => <p key={j} className="text-xs ml-2">- {r}</p>)}
            </div>
          ))}
        </div>
      )}

      {/* Modality Contribution */}
      <div className="bg-slate-800 rounded-xl p-4 mb-6">
        <h3 className="text-sm text-slate-400 mb-3">모달리티별 기여도</h3>
        {[
          { key: 'voice', label: '음성 분석', weight: 0.30 },
          { key: 'face', label: '표정 분석', weight: 0.30 },
          { key: 'hr', label: '심박수 분석', weight: 0.40 },
        ].map(({ key, label, weight }) => (
          <div key={key} className="mb-2">
            <div className="flex justify-between text-sm mb-1">
              <span>{label}</span>
              <span>{(weight * 100).toFixed(0)}%</span>
            </div>
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500" style={{ width: `${weight * 100}%` }} />
            </div>
          </div>
        ))}
      </div>

      {/* Action */}
      <button
        onClick={() => setPhase('home')}
        className="w-full py-3 bg-slate-700 hover:bg-slate-600 rounded-xl font-semibold transition-colors"
      >
        새 테스트
      </button>
    </div>
  );
}
