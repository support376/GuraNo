import { useState } from 'react';
import { useSessionStore } from '@/stores/sessionStore';
import { useQuestionStore } from '@/stores/questionStore';
import { sessionApi, questionApi } from '@/services/api';
import { useCamera } from '@/hooks/useCamera';
import type { HRSource } from '@/types/heartrate';

export default function SetupPage() {
  const { setSession, setPhase, setHRSource } = useSessionStore();
  const { drafts, addDraft, removeDraft, updateDraft } = useQuestionStore();
  const setQuestions = useQuestionStore((s) => s.setQuestions);
  const camera = useCamera();
  const [selectedHR, setSelectedHR] = useState<HRSource>('rppg');
  const [cameraReady, setCameraReady] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCameraTest = async () => {
    await camera.start();
    setCameraReady(true);
  };

  const handleStart = async () => {
    const validQuestions = drafts.filter((d) => d.trim().length > 0);
    if (validQuestions.length === 0) return;

    setLoading(true);
    try {
      const session = await sessionApi.create(selectedHR);
      setSession(session);
      setHRSource(selectedHR);

      const questions = await questionApi.bulkCreate(
        session.id,
        validQuestions.map((text) => ({ text, category: 'sensitive' }))
      );
      setQuestions(questions);
      camera.stop();
      setPhase('calibration');
    } catch (e: any) {
      console.error(e);
      setError(e?.response?.data?.detail || e?.message || '서버 연결에 실패했습니다. 백엔드가 실행 중인지 확인하세요.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">테스트 설정</h2>

      {/* Question Editor */}
      <div className="bg-slate-800 rounded-xl p-4 mb-6">
        <h3 className="text-sm text-slate-400 mb-3">질문 입력</h3>
        <div className="space-y-2">
          {drafts.map((d, i) => (
            <div key={i} className="flex gap-2">
              <span className="text-slate-500 mt-2 text-sm w-8">Q{i + 1}</span>
              <input
                type="text"
                value={d}
                onChange={(e) => updateDraft(i, e.target.value)}
                placeholder="질문을 입력하세요..."
                className="flex-1 bg-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {drafts.length > 1 && (
                <button
                  onClick={() => removeDraft(i)}
                  className="text-slate-500 hover:text-red-400 px-2"
                >
                  X
                </button>
              )}
            </div>
          ))}
        </div>
        <button
          onClick={() => addDraft('')}
          className="mt-3 text-sm text-blue-400 hover:text-blue-300"
        >
          + 질문 추가
        </button>
      </div>

      {/* Device Connection */}
      <div className="bg-slate-800 rounded-xl p-4 mb-6">
        <h3 className="text-sm text-slate-400 mb-3">기기 연결</h3>

        <div className="space-y-3">
          {/* Camera */}
          <div className="flex items-center justify-between">
            <span>카메라</span>
            {cameraReady ? (
              <span className="text-truth text-sm">연결됨</span>
            ) : (
              <button onClick={handleCameraTest} className="text-sm bg-slate-700 px-3 py-1 rounded-lg hover:bg-slate-600">
                테스트
              </button>
            )}
          </div>

          {/* Camera preview */}
          {cameraReady && (
            <div className="rounded-lg overflow-hidden bg-black aspect-video max-h-48">
              <video ref={camera.videoRef} autoPlay muted playsInline className="w-full h-full object-cover" />
            </div>
          )}

          {/* HR Source */}
          <div className="pt-2">
            <span className="text-sm text-slate-400">심박수 소스</span>
            <div className="mt-2 space-y-1">
              {([
                ['apple_watch', 'Apple Watch (권장)'],
                ['ble', 'BLE 심박 밴드'],
                ['rppg', '웹캠 rPPG (대안)'],
                ['none', '사용 안 함'],
              ] as [HRSource, string][]).map(([value, label]) => (
                <label key={value} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="radio"
                    name="hr"
                    checked={selectedHR === value}
                    onChange={() => setSelectedHR(value)}
                    className="accent-blue-500"
                  />
                  {label}
                </label>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/30 border border-red-500/30 rounded-xl p-3 mb-4 text-sm text-red-300">
          {error}
        </div>
      )}

      {/* Start Button */}
      <button
        onClick={handleStart}
        disabled={loading || drafts.filter((d) => d.trim()).length === 0}
        className="w-full py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:text-slate-500 rounded-xl text-lg font-semibold transition-colors"
      >
        {loading ? '준비 중...' : '테스트 시작'}
      </button>

      <button
        onClick={() => setPhase('home')}
        className="w-full mt-3 py-2 text-slate-500 hover:text-slate-300 text-sm"
      >
        돌아가기
      </button>
    </div>
  );
}
