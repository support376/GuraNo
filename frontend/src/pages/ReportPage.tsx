import { useEffect, useState } from 'react';
import { useSessionStore } from '@/stores/sessionStore';
import { useResultStore } from '@/stores/resultStore';
import { reportApi } from '@/services/api';
import type { ReportData } from '@/types/analysis';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer,
} from 'recharts';

export default function ReportPage() {
  const { session, setPhase } = useSessionStore();
  const storeReport = useResultStore((s) => s.report);
  const setReport = useResultStore((s) => s.setReport);
  const [report, setLocalReport] = useState<ReportData | null>(storeReport);
  const [loading, setLoading] = useState(!storeReport);

  useEffect(() => {
    if (!storeReport && session) {
      reportApi.get(session.id).then((r) => {
        setReport(r);
        setLocalReport(r);
        setLoading(false);
      }).catch(() => setLoading(false));
    }
  }, [session, storeReport, setReport]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-slate-400">보고서를 불러오는 중...</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-slate-400">보고서를 찾을 수 없습니다.</p>
        <button onClick={() => setPhase('home')} className="text-blue-400 hover:text-blue-300">
          홈으로 돌아가기
        </button>
      </div>
    );
  }

  const hrData = report.hr_timeline ? report.hr_timeline.timestamps.map((ts, i) => ({
    time: new Date(ts * 1000).toLocaleTimeString('ko-KR', { minute: '2-digit', second: '2-digit' }),
    bpm: report.hr_timeline!.bpm[i],
  })) : [];

  const getVerdictStyle = (verdict: string | null) => {
    if (verdict === '거짓') return 'text-lie bg-lie/10 border-lie/30';
    if (verdict === '의심') return 'text-suspect bg-suspect/10 border-suspect/30';
    return 'text-truth bg-truth/10 border-truth/30';
  };

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold mb-1">GuraNo 분석 보고서</h2>
      <p className="text-sm text-slate-500 mb-6">{session?.created_at ? new Date(session.created_at).toLocaleString('ko-KR') : ''}</p>

      {/* Truth Score */}
      <div className="bg-slate-800 rounded-xl p-6 mb-6 text-center">
        <p className="text-sm text-slate-400 mb-2">종합 진실성 점수</p>
        <p className={`text-5xl font-bold ${
          report.truth_score >= 70 ? 'text-truth' : report.truth_score >= 50 ? 'text-suspect' : 'text-lie'
        }`}>
          {report.truth_score.toFixed(0)}%
        </p>
        <div className="h-3 bg-slate-700 rounded-full overflow-hidden mt-4 max-w-xs mx-auto">
          <div
            className={`h-full rounded-full ${
              report.truth_score >= 70 ? 'bg-truth' : report.truth_score >= 50 ? 'bg-suspect' : 'bg-lie'
            }`}
            style={{ width: `${report.truth_score}%` }}
          />
        </div>
        <p className="text-sm text-slate-400 mt-2">
          {report.total_questions}개 답변 중 {report.lie_count}개 거짓, {report.suspect_count}개 의심
        </p>
      </div>

      {/* HR Chart */}
      {hrData.length > 0 && (
        <div className="bg-slate-800 rounded-xl p-4 mb-6">
          <h3 className="text-sm text-slate-400 mb-3">심박수 변화</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={hrData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} domain={['auto', 'auto']} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              {session?.baseline_hr && (
                <ReferenceLine y={session.baseline_hr} stroke="#3b82f6" strokeDasharray="5 5" label="기준선" />
              )}
              <Line type="monotone" dataKey="bpm" stroke="#ef4444" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
          {report.hr_peak_bpm && (
            <div className="flex justify-between text-xs text-slate-500 mt-2">
              <span>최고: {report.hr_peak_bpm.toFixed(0)} BPM ({report.hr_peak_question})</span>
              <span>최저: {report.hr_lowest_bpm?.toFixed(0)} BPM ({report.hr_lowest_question})</span>
            </div>
          )}
        </div>
      )}

      {/* Question Results */}
      <div className="space-y-3 mb-6">
        <h3 className="text-sm text-slate-400">질문별 상세</h3>
        {report.answers.map((a, i) => (
          <div key={i} className={`border rounded-xl p-4 ${getVerdictStyle(a.verdict)}`}>
            <div className="flex justify-between items-start mb-2">
              <span className="text-xs text-slate-400">Q{i + 1}</span>
              <span className="text-sm font-semibold">
                {a.verdict === '거짓' ? '거짓' : a.verdict === '의심' ? '의심' : '진실'}
                {a.fusion_score != null && ` (${(a.fusion_score * 100).toFixed(0)}%)`}
              </span>
            </div>
            {a.transcript && <p className="text-sm mb-2">A: "{a.transcript}"</p>}
            {a.hr_bpm != null && (
              <p className="text-xs text-slate-400">심박수: {a.hr_bpm.toFixed(0)} BPM</p>
            )}
            {a.reasons && (a.reasons as unknown as { reasons: string[] }).reasons && (
              <ul className="mt-2 text-xs space-y-1">
                {((a.reasons as unknown as { reasons: string[] }).reasons).map((r, j) => (
                  <li key={j}>- {r}</li>
                ))}
              </ul>
            )}
            {a.screenshot_path && (
              <img src={a.screenshot_path} alt="캡처" className="mt-2 rounded-lg max-h-32 object-cover" />
            )}
          </div>
        ))}
      </div>

      {/* Modality Contribution */}
      {report.modality_weights && (
        <div className="bg-slate-800 rounded-xl p-4 mb-6">
          <h3 className="text-sm text-slate-400 mb-3">모달리티별 기여도</h3>
          {Object.entries(report.modality_weights).map(([key, val]) => {
            const labels: Record<string, string> = { voice: '음성 분석', face: '표정 분석', hr: '심박수 분석' };
            return (
              <div key={key} className="mb-2">
                <div className="flex justify-between text-sm mb-1">
                  <span>{labels[key] || key}</span>
                  <span>{((val as number) * 100).toFixed(0)}%</span>
                </div>
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500" style={{ width: `${(val as number) * 100}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        {report.pdf_path && (
          <a
            href={`/api/reports/session/${session?.id}/pdf`}
            className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 rounded-xl text-center font-semibold transition-colors"
          >
            PDF 다운로드
          </a>
        )}
        <button
          onClick={() => setPhase('home')}
          className="flex-1 py-3 bg-slate-700 hover:bg-slate-600 rounded-xl font-semibold transition-colors"
        >
          새 테스트
        </button>
      </div>
    </div>
  );
}
