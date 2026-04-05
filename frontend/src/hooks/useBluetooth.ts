import { useRef, useState, useCallback } from 'react';

export function useBluetooth(onHeartRate: (bpm: number) => void) {
  const [connected, setConnected] = useState(false);
  const [deviceName, setDeviceName] = useState<string | null>(null);
  const deviceRef = useRef<BluetoothDevice | null>(null);

  const connect = useCallback(async () => {
    try {
      if (!navigator.bluetooth) {
        throw new Error('Web Bluetooth is not supported');
      }

      const device = await navigator.bluetooth.requestDevice({
        filters: [{ services: ['heart_rate'] }],
      });

      deviceRef.current = device;
      setDeviceName(device.name ?? 'Unknown');

      const server = await device.gatt!.connect();
      const service = await server.getPrimaryService('heart_rate');
      const characteristic = await service.getCharacteristic('heart_rate_measurement');

      await characteristic.startNotifications();
      characteristic.addEventListener('characteristicvaluechanged', (event: Event) => {
        const value = (event.target as BluetoothRemoteGATTCharacteristic).value!;
        const flags = value.getUint8(0);
        const is16Bit = flags & 0x1;
        const bpm = is16Bit ? value.getUint16(1, true) : value.getUint8(1);
        onHeartRate(bpm);
      });

      setConnected(true);
    } catch (err) {
      console.error('BLE connection failed:', err);
      setConnected(false);
    }
  }, [onHeartRate]);

  const disconnect = useCallback(() => {
    deviceRef.current?.gatt?.disconnect();
    deviceRef.current = null;
    setConnected(false);
    setDeviceName(null);
  }, []);

  return { connected, deviceName, connect, disconnect };
}
