import { useSessionStore } from '@/stores/sessionStore';
import { useResultStore } from '@/stores/resultStore';
import { sessionApi } from '@/services/api';
import { useState, useEffect } from 'react';
import type { Session } from '@/types/session';

export default function HomePage() {
  const { setSession, setPhase } = useSessionStore();
  const reset = useResultStore((s) => s.reset);
  const [pastSessions, setPastSessions] = useState<Session[]>([]);

  useEffect(() => {
    sessionApi.list().then(setPastSessions).catch(() => {});
  }, []);

  const startNew = async () => {
    reset();
    setPhase('setup');
  };

  const viewReport = (session: Session) => {
    setSession(session);
    setPhase('report');
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6">
      <div className="max-w-md w-full text-center">
        <h1 className="text-5xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
          GuraNo
        </h1>
        <p className="text-slate-400 text-lg mb-10">AI 거짓말 탐지기</p>

        <button
          onClick={startNew}
          className="w-full py-4 bg-blue-600 hover:bg-blue-700 rounded-xl text-lg font-semibold transition-colors mb-4"
        >
          새 테스트 시작하기
        </button>

        {pastSessions.length > 0 && (
          <div className="mt-8">
            <h3 className="text-sm text-slate-500 mb-3 text-left">이전 보고서</h3>
            <div className="space-y-2">
              {pastSessions.slice(0, 5).map((s) => (
                <button
                  key={s.id}
                  onClick={() => viewReport(s)}
                  className="w-full p-3 bg-slate-800 hover:bg-slate-700 rounded-lg text-left text-sm transition-colors flex justify-between"
                >
                  <span>{new Date(s.created_at).toLocaleString('ko-KR')}</span>
                  <span className={s.truth_score ? (s.truth_score >= 70 ? 'text-truth' : s.truth_score >= 50 ? 'text-suspect' : 'text-lie') : 'text-slate-500'}>
                    {s.truth_score ? `${s.truth_score.toFixed(0)}%` : s.status}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        <p className="text-xs text-slate-600 mt-12">
          PC: 웹캠 + 마이크 | 모바일: 전면카메라 + 마이크
        </p>
      </div>
    </div>
  );
}
