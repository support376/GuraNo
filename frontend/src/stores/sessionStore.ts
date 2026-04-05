import { create } from 'zustand';
import type { Session } from '@/types/session';
import type { HRSource } from '@/types/heartrate';

interface SessionState {
  session: Session | null;
  phase: 'home' | 'setup' | 'calibration' | 'session' | 'report';
  hrSource: HRSource;
  setSession: (s: Session) => void;
  setPhase: (p: SessionState['phase']) => void;
  setHRSource: (s: HRSource) => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  session: null,
  phase: 'home',
  hrSource: 'none',
  setSession: (session) => set({ session }),
  setPhase: (phase) => set({ phase }),
  setHRSource: (hrSource) => set({ hrSource }),
}));
