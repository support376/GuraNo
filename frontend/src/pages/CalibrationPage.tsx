import { useEffect, useState, useCallback, useRef } from 'react';
import { useSessionStore } from '@/stores/sessionStore';
import { useCamera } from '@/hooks/useCamera';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { WSMessage } from '@/types/websocket';

export default function CalibrationPage() {
  const { session, setPhase } = useSessionStore();
  const camera = useCamera();
  const [status, setStatus] = useState('카메라를 준비하고 있습니다...');
  const [baselineReady, setBaselineReady] = useState(false);
  const [countdown, setCountdown] = useState(10); // 10초로 줄임
  const [calibrating, setCalibrating] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval>>();

  const handleWS = useCallback((msg: WSMessage) => {
    if (msg.type === 'status') {
      setStatus(msg.message as string);
    } else if (msg.type === 'baseline_ready') {
      setBaselineReady(true);
      setCalibrating(false);
      setStatus('기준선 수립 완료!');
    }
  }, []);

  const { send, connected } = useWebSocket(session?.id ?? null, handleWS);

  // 카메라 바로 시작
  useEffect(() => {
    camera.start();
    return () => camera.stop();
  }, []);

  // 카메라 켜지면 상태 업데이트
  useEffect(() => {
    if (camera.active) {
      setStatus('카메라 연결됨. 기준선 수집을 시작하세요.');
    }
  }, [camera.active]);

  // 비디오 프레임 전송
  useEffect(() => {
    if (!camera.active || !connected) return;
    const interval = setInterval(() => {
      const frame = camera.captureFrame();
      if (frame) {
        send({ type: 'video_frame', data: frame, ts: Date.now() / 1000 });
      }
    }, 200); // 5fps during calibration
    return () => clearInterval(interval);
  }, [camera.active, connected, send, camera.captureFrame]);

  const startCalibration = () => {
    setCalibrating(true);
    setStatus('기준선 수집 중... 편안하게 앉아 계세요.');
    if (connected) {
      send({ type: 'calibration_start' });
    }

    let t = 10;
    setCountdown(t);
    timerRef.current = setInterval(() => {
      t -= 1;
      setCountdown(t);
      if (t <= 0) {
        clearInterval(timerRef.current);
        if (connected) {
          send({ type: 'calibration_done' });
        }
        // 서버 응답 없어도 자동 완료
        setBaselineReady(true);
        setCalibrating(false);
        setStatus('기준선 수립 완료!');
      }
    }, 1000);
  };

  const proceedToSession = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    camera.stop();
    setPhase('session');
  };

  const skipCalibration = () => {
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
            <video ref={camera.videoRef} autoPlay muted playsInline className="w-full h-full object-cover" />
          </div>

          {/* Connection Status */}
          <div className="flex items-center justify-center gap-2 mb-3">
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-yellow-500'}`} />
            <span className="text-xs text-slate-400">
              {connected ? '서버 연결됨' : '서버 미연결 (로컬 모드)'}
            </span>
          </div>

          <p className="text-slate-300 mb-4">{status}</p>

          {/* Calibrating - show progress */}
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

          {/* Start button */}
          {!baselineReady && !calibrating && (
            <button
              onClick={startCalibration}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors"
            >
              기준선 수집 시작 (10초)
            </button>
          )}

          {/* Done - proceed */}
          {baselineReady && (
            <button
              onClick={proceedToSession}
              className="w-full py-3 bg-green-600 hover:bg-green-700 rounded-lg font-semibold transition-colors"
            >
              테스트 시작
            </button>
          )}
        </div>

        {/* Skip button always visible */}
        {!baselineReady && (
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
