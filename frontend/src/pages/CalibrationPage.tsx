import { useEffect, useState, useCallback, useRef } from 'react';
import { useSessionStore } from '@/stores/sessionStore';
import { useCamera } from '@/hooks/useCamera';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { WSMessage } from '@/types/websocket';

export default function CalibrationPage() {
  const { session, setPhase } = useSessionStore();
  const camera = useCamera();
  const [baselineReady, setBaselineReady] = useState(false);
  const [countdown, setCountdown] = useState(10);
  const [calibrating, setCalibrating] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval>>();

  const handleWS = useCallback((msg: WSMessage) => {
    if (msg.type === 'baseline_ready') {
      setBaselineReady(true);
      setCalibrating(false);
    }
  }, []);

  const { send, connected } = useWebSocket(session?.id ?? null, handleWS);

  // 비디오 프레임 전송
  useEffect(() => {
    if (!camera.active || !connected) return;
    const interval = setInterval(() => {
      const frame = camera.captureFrame();
      if (frame) {
        send({ type: 'video_frame', data: frame, ts: Date.now() / 1000 });
      }
    }, 200);
    return () => clearInterval(interval);
  }, [camera.active, connected, send, camera.captureFrame]);

  // 카메라 켜기 + 기준선 동시에 시작 (버튼 터치로)
  const startCalibration = async () => {
    await camera.start(); // 사용자 터치 이벤트 안에서 호출
    setCalibrating(true);
    if (connected) send({ type: 'calibration_start' });

    let t = 10;
    setCountdown(t);
    timerRef.current = setInterval(() => {
      t -= 1;
      setCountdown(t);
      if (t <= 0) {
        clearInterval(timerRef.current);
        if (connected) send({ type: 'calibration_done' });
        setBaselineReady(true);
        setCalibrating(false);
      }
    }, 1000);
  };

  const proceedToSession = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    // 카메라는 끄지 않음 - SessionPage에서 새로 시작
    camera.stop();
    setPhase('session');
  };

  const skipCalibration = async () => {
    if (timerRef.current) clearInterval(timerRef.current);
    camera.stop();
    setPhase('session');
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6">
      <div className="max-w-md w-full text-center">
        <h2 className="text-2xl font-bold mb-4">기준선 수립</h2>

        <div className="bg-slate-800 rounded-xl p-6 mb-6">
          {/* Camera Preview */}
          <div className="rounded-lg overflow-hidden bg-black aspect-video mb-4">
            {camera.active ? (
              <video ref={camera.videoRef} autoPlay muted playsInline className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-slate-500">
                카메라 대기 중
              </div>
            )}
          </div>

          {/* Status */}
          <div className="flex items-center justify-center gap-2 mb-3">
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-yellow-500'}`} />
            <span className="text-xs text-slate-400">
              {connected ? '서버 연결됨' : '서버 미연결 (로컬 모드)'}
            </span>
          </div>

          <p className="text-slate-300 mb-4">
            {calibrating ? '기준선 수집 중... 편안하게 앉아 계세요.' :
             baselineReady ? '기준선 수립 완료!' :
             '아래 버튼을 눌러 카메라를 켜고 기준선을 수집합니다.'}
          </p>

          {camera.error && (
            <p className="text-red-400 text-sm mb-3">{camera.error}</p>
          )}

          {/* Calibrating progress */}
          {calibrating && (
            <div className="mb-4">
              <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all duration-1000"
                  style={{ width: `${((10 - countdown) / 10) * 100}%` }}
                />
              </div>
              <p className="text-sm text-slate-400 mt-1">{countdown}초 남음</p>
            </div>
          )}

          {/* Start button - 카메라 + 기준선 동시 시작 */}
          {!baselineReady && !calibrating && (
            <button
              onClick={startCalibration}
              className="w-full py-4 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors text-lg"
            >
              카메라 켜고 기준선 수집 (10초)
            </button>
          )}

          {/* Done */}
          {baselineReady && (
            <button
              onClick={proceedToSession}
              className="w-full py-4 bg-green-600 hover:bg-green-700 rounded-lg font-semibold transition-colors text-lg"
            >
              테스트 시작
            </button>
          )}
        </div>

        {!baselineReady && !calibrating && (
          <button
            onClick={skipCalibration}
            className="text-slate-500 hover:text-slate-300 text-sm"
          >
            건너뛰고 바로 테스트 시작
          </button>
        )}
      </div>
    </div>
  );
}
