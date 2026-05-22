import { Platform } from 'react-native';

export type SoundType = 'tap' | 'success' | 'error' | 'notify';

const soundMap: Record<SoundType, { frequency: number; duration: number; type: OscillatorType }> = {
  tap: { frequency: 520, duration: 0.045, type: 'sine' },
  success: { frequency: 740, duration: 0.09, type: 'triangle' },
  error: { frequency: 180, duration: 0.12, type: 'sawtooth' },
  notify: { frequency: 620, duration: 0.08, type: 'sine' },
};

export function playSleekSound(type: SoundType = 'tap') {
  if (Platform.OS !== 'web') return;
  try {
    const AudioContextClass = (globalThis as any).AudioContext || (globalThis as any).webkitAudioContext;
    if (!AudioContextClass) return;
    const audio = new AudioContextClass();
    const osc = audio.createOscillator();
    const gain = audio.createGain();
    const config = soundMap[type];
    osc.type = config.type;
    osc.frequency.value = config.frequency;
    gain.gain.setValueAtTime(0.0001, audio.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.08, audio.currentTime + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, audio.currentTime + config.duration);
    osc.connect(gain);
    gain.connect(audio.destination);
    osc.start();
    osc.stop(audio.currentTime + config.duration + 0.02);
    setTimeout(() => audio.close().catch(() => {}), 220);
  } catch (error) {
    // Audio should never block UI interaction.
  }
}
