import { create } from 'zustand';
import type { AnalysisResult, LieDetection, ReportData } from '@/types/analysis';

interface ResultState {
  latestResult: AnalysisResult | null;
  lieDetections: LieDetection[];
  hrHistory: { ts: number; bpm: number }[];
  report: ReportData | null;
  setLatestResult: (r: AnalysisResult) => void;
  addLieDetection: (d: LieDetection) => void;
  addHRReading: (ts: number, bpm: number) => void;
  setReport: (r: ReportData) => void;
  reset: () => void;
}

export const useResultStore = create<ResultState>((set) => ({
  latestResult: null,
  lieDetections: [],
  hrHistory: [],
  report: null,
  setLatestResult: (latestResult) => set({ latestResult }),
  addLieDetection: (d) => set((s) => ({ lieDetections: [...s.lieDetections, d] })),
  addHRReading: (ts, bpm) =>
    set((s) => ({ hrHistory: [...s.hrHistory, { ts, bpm }] })),
  setReport: (report) => set({ report }),
  reset: () => set({ latestResult: null, lieDetections: [], hrHistory: [], report: null }),
}));
