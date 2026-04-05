export interface AnalysisResult {
  ts: number;
  voice_score: number;
  face_score: number;
  hr_score: number;
  fusion_score: number;
  verdict: string;
  current_hr: number;
  baseline_hr: number;
  transcript?: string;
}

export interface LieDetection {
  ts: number;
  confidence: number;
  screenshot_url: string;
  transcript: string;
  reasons: string[];
  question_text?: string;
}

export interface AnswerResult {
  question_id: string;
  transcript: string | null;
  voice_score: number | null;
  face_score: number | null;
  hr_score: number | null;
  fusion_score: number | null;
  verdict: string | null;
  hr_bpm: number | null;
  reasons: { reasons: string[] } | null;
  screenshot_path: string | null;
}

export interface ReportData {
  id: string;
  session_id: string;
  truth_score: number;
  total_questions: number;
  lie_count: number;
  suspect_count: number;
  truth_count: number;
  hr_peak_bpm: number | null;
  hr_peak_question: string | null;
  hr_lowest_bpm: number | null;
  hr_lowest_question: string | null;
  modality_weights: Record<string, number> | null;
  hr_timeline: { timestamps: number[]; bpm: number[]; questions: string[] } | null;
  pdf_path: string | null;
  answers: AnswerResult[];
}
