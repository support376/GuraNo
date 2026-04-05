export type HRSource = 'apple_watch' | 'ble' | 'rppg' | 'none';

export interface HeartRateReading {
  bpm: number;
  source: HRSource;
  timestamp: number;
}
