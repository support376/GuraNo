/**
 * WebSocket message protocol types and helpers.
 */
import type { WSMessage } from '@/types/websocket';

export function createVideoFrameMessage(base64: string): WSMessage {
  return { type: 'video_frame', data: base64, ts: Date.now() / 1000 };
}

export function createAudioChunkMessage(base64: string): WSMessage {
  return { type: 'audio_chunk', data: base64, ts: Date.now() / 1000 };
}

export function createHeartRateMessage(bpm: number, source: string): WSMessage {
  return { type: 'heart_rate', bpm, source, ts: Date.now() / 1000 };
}

export function createControlMessage(type: WSMessage['type']): WSMessage {
  return { type };
}
