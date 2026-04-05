export type WSMessageType =
  | 'video_frame'
  | 'audio_chunk'
  | 'heart_rate'
  | 'session_start'
  | 'session_stop'
  | 'calibration_start'
  | 'calibration_done'
  | 'next_question'
  | 'analysis_result'
  | 'lie_detected'
  | 'tts_play'
  | 'baseline_ready'
  | 'session_complete'
  | 'status';

export interface WSMessage {
  type: WSMessageType;
  [key: string]: unknown;
}
