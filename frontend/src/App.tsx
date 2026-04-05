import { useSessionStore } from '@/stores/sessionStore';
import HomePage from '@/pages/HomePage';
import SetupPage from '@/pages/SetupPage';
import CalibrationPage from '@/pages/CalibrationPage';
import SessionPage from '@/pages/SessionPage';
import ReportPage from '@/pages/ReportPage';

export default function App() {
  const phase = useSessionStore((s) => s.phase);

  return (
    <div className="min-h-screen bg-slate-900">
      {phase === 'home' && <HomePage />}
      {phase === 'setup' && <SetupPage />}
      {phase === 'calibration' && <CalibrationPage />}
      {phase === 'session' && <SessionPage />}
      {phase === 'report' && <ReportPage />}
    </div>
  );
}
