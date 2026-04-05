import { useEffect, useState, useCallback } from 'react';
import { useSessionStore } from '@/stores/sessionStore';
import { useCamera } from '@/hooks/useCamera';
import { useMicrophone } from '@/hooks/useMicrophone';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { WSMessage } from '@/types/websocket';

export default function CalibrationPage() {
  const { session, setPhase } = useSessionStore();
  const camera = useCamera();
  const [status, setStatus] = useState('기기 연결 중...');
  const [baselineReady, setBaselineReady] = useState(false);
  const [countdown, setCountdown] = useState(30);

  const handleWS = useCallback((msg: WSMessage) => {
    if (msg.type === 'status') {
      setStatus(msg.message as string);
    } else if (msg.type === 'baseline_ready') {
      setBaselineReady(true);
      setStatus('기준선 수립이 완료되었습니다!');
    }
  }, []);

  const { send, connected } = useWebSocket(session?.id ?? null, handleWS);

  const handleAudioChunk = useCallback((base64: string) => {
    send({ type: 'audio_chunk', data: base64, ts: Date.now() / 1000 });
  }, [send]);

  const mic = useMicrophone(handleAudioChunk);

  // Start devices when connected
  useEffect(() => {
    if (connected) {
      camera.start();
      mic.start();
    }
  }, [connected]);

  // Send video frames
  useEffect(() => {
    if (!camera.active || !connected) return;
    const interval = setInterval(() => {
      const frame = camera.captureFrame();
      if (frame) {
        send({ type: 'video_frame', data: frame, ts: Date.now() / 1000 });
      }
    }, 100); // 10fps during calibration
    return () => clearInterval(interval);
  }, [camera.active, connected, send, camera.captureFrame]);

  // Start calibration
  const startCalibration = () => {
    send({ type: 'calibration_start' });
    setStatus('기준선을 수집하고 있습니다. 편안하게 앉아 계세요...');
    // Countdown
    let t = 30;
    const timer = setInterval(() => {
      t -= 1;
      setCountdown(t);
      if (t <= 0) {
        clearInterval(timer);
        send({ type: 'calibration_done' });
      }
    }, 1000);
  };

  const proceedToSession = () => {
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

          <p className="text-slate-300 mb-4">{status}</p>

          {!baselineReady && countdown < 30 && (
            <div className="mb-4">
              <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all duration-1000"
                  style={{ width: `${((30 - countdown) / 30) * 100}%` }}
                />
              </div>
              <p className="text-sm text-slate-400 mt-1">{countdown}초 남음</p>
            </div>
          )}

          {!baselineReady && countdown === 30 && (
            <button
              onClick={startCalibration}
              disabled={!connected}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 rounded-lg font-semibold transition-colors"
            >
              {connected ? '기준선 수집 시작' : '연결 중...'}
            </button>
          )}

          {baselineReady && (
            <button
              onClick={proceedToSession}
              className="w-full py-3 bg-green-600 hover:bg-green-700 rounded-lg font-semibold transition-colors"
            >
              테스트 시작
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
