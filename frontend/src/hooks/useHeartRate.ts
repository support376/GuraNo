import { useState, useCallback, useRef } from 'react';
import type { HRSource, HeartRateReading } from '@/types/heartrate';

export function useHeartRate() {
  const [bpm, setBpm] = useState(0);
  const [source, setSource] = useState<HRSource>('none');
  const [connected, setConnected] = useState(false);
  const bleDeviceRef = useRef<BluetoothDevice | null>(null);
  const onReadingRef = useRef<((reading: HeartRateReading) => void) | null>(null);

  const setOnReading = useCallback((cb: (reading: HeartRateReading) => void) => {
    onReadingRef.current = cb;
  }, []);

  // BLE Heart Rate connection (Web Bluetooth API)
  const connectBLE = useCallback(async () => {
    try {
      const device = await navigator.bluetooth.requestDevice({
        filters: [{ services: ['heart_rate'] }],
      });
      bleDeviceRef.current = device;
      const server = await device.gatt!.connect();
      const service = await server.getPrimaryService('heart_rate');
      const characteristic = await service.getCharacteristic('heart_rate_measurement');

      await characteristic.startNotifications();
      characteristic.addEventListener('characteristicvaluechanged', (event: Event) => {
        const value = (event.target as BluetoothRemoteGATTCharacteristic).value!;
        const flags = value.getUint8(0);
        const rate16 = flags & 0x1;
        const hrValue = rate16 ? value.getUint16(1, true) : value.getUint8(1);
        setBpm(hrValue);
        const reading: HeartRateReading = {
          bpm: hrValue,
          source: 'ble',
          timestamp: Date.now() / 1000,
        };
        onReadingRef.current?.(reading);
      });

      setSource('ble');
      setConnected(true);
    } catch {
      setConnected(false);
    }
  }, []);

  // Manual HR update (from Apple Watch via WebSocket or rPPG)
  const updateHR = useCallback((newBpm: number, hrSource: HRSource) => {
    setBpm(newBpm);
    setSource(hrSource);
    setConnected(true);
    onReadingRef.current?.({
      bpm: newBpm,
      source: hrSource,
      timestamp: Date.now() / 1000,
    });
  }, []);

  const disconnect = useCallback(() => {
    bleDeviceRef.current?.gatt?.disconnect();
    bleDeviceRef.current = null;
    setConnected(false);
    setBpm(0);
    setSource('none');
  }, []);

  return { bpm, source, connected, connectBLE, updateHR, disconnect, setOnReading };
}
