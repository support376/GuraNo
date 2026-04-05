export interface Session {
  id: string;
  status: string;
  hr_source: string;
  baseline_hr: number | null;
  baseline_hrv: number | null;
  truth_score: number | null;
  created_at: string;
}
