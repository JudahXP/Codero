import React, { createContext, ReactNode, useContext, useEffect, useMemo, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SystemUI from 'expo-system-ui';
import { api } from '../services/api';
import { playSleekSound, SoundType } from '../services/sound';
import { useAuth } from './AuthContext';

export interface AppSettings {
  font_size: 'small' | 'medium' | 'large';
  high_contrast: boolean;
  reduced_motion: boolean;
  sound_effects: boolean;
  notifications: boolean;
  daily_reminder: boolean;
  email_login: boolean;
  email_join: boolean;
  email_vip: boolean;
  email_daily: boolean;
  theme: 'dark' | 'light';
}

export const defaultSettings: AppSettings = {
  font_size: 'medium',
  high_contrast: false,
  reduced_motion: false,
  sound_effects: true,
  notifications: true,
  daily_reminder: true,
  email_login: true,
  email_join: true,
  email_vip: true,
  email_daily: true,
  theme: 'dark',
};

export const palettes = {
  dark: {
    background: '#0D0D0D',
    backgroundAlt: '#1A1A2E',
    surface: 'rgba(255,255,255,0.06)',
    surfaceStrong: '#1E1E2F',
    card: '#202033',
    text: '#FFFFFF',
    textMuted: '#AAB0BE',
    border: 'rgba(255,255,255,0.16)',
    primary: '#00FF88',
    primaryText: '#0D0D0D',
    danger: '#FF6B6B',
    warning: '#FFD700',
    info: '#00BFFF',
  },
  light: {
    background: '#F6F8FB',
    backgroundAlt: '#E9F5FF',
    surface: 'rgba(13,24,38,0.06)',
    surfaceStrong: '#FFFFFF',
    card: '#FFFFFF',
    text: '#111827',
    textMuted: '#5B6472',
    border: 'rgba(17,24,39,0.14)',
    primary: '#047857',
    primaryText: '#FFFFFF',
    danger: '#DC2626',
    warning: '#B45309',
    info: '#0369A1',
  },
  contrast: {
    background: '#000000',
    backgroundAlt: '#000000',
    surface: '#111111',
    surfaceStrong: '#000000',
    card: '#050505',
    text: '#FFFFFF',
    textMuted: '#FFFFFF',
    border: '#FFFFFF',
    primary: '#FFFF00',
    primaryText: '#000000',
    danger: '#FF3B30',
    warning: '#FFFF00',
    info: '#00FFFF',
  },
};

interface SettingsContextType {
  settings: AppSettings;
  colors: typeof palettes.dark;
  fontScale: number;
  gradient: readonly [string, string, string];
  updateSetting: <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => Promise<void>;
  saveSettings: (next: Partial<AppSettings>) => Promise<void>;
  playSound: (type?: SoundType) => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);

  useEffect(() => {
    loadLocalSettings();
  }, []);

  useEffect(() => {
    if (user?.settings) {
      const merged = { ...defaultSettings, ...settings, ...user.settings };
      setSettings(merged);
      AsyncStorage.setItem('app_settings', JSON.stringify(merged)).catch(() => {});
    }
  }, [user?.id, JSON.stringify(user?.settings || {})]);

  useEffect(() => {
    const c = settings.high_contrast ? palettes.contrast : palettes[settings.theme];
    SystemUI.setBackgroundColorAsync(c.background).catch(() => {});
  }, [settings.theme, settings.high_contrast]);

  const loadLocalSettings = async () => {
    try {
      const raw = await AsyncStorage.getItem('app_settings');
      if (raw) {
        setSettings({ ...defaultSettings, ...JSON.parse(raw) });
      }
    } catch (error) {
      setSettings(defaultSettings);
    }
  };

  const saveSettings = async (next: Partial<AppSettings>) => {
    const merged = { ...defaultSettings, ...settings, ...next };
    setSettings(merged);
    await AsyncStorage.setItem('app_settings', JSON.stringify(merged));
    if (user) {
      await api.put('/settings', { settings: merged });
    }
  };

  const updateSetting = async <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    await saveSettings({ [key]: value } as Partial<AppSettings>);
  };

  const colors = settings.high_contrast ? palettes.contrast : palettes[settings.theme];
  const fontScale = settings.font_size === 'small' ? 0.9 : settings.font_size === 'large' ? 1.18 : 1;
  const gradient = useMemo(() => [colors.background, colors.backgroundAlt, colors.background] as const, [colors]);

  const playSound = (type: SoundType = 'tap') => {
    if (settings.sound_effects) playSleekSound(type);
  };

  return (
    <SettingsContext.Provider value={{ settings, colors, fontScale, gradient, updateSetting, saveSettings, playSound }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useAppSettings() {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useAppSettings must be used inside SettingsProvider');
  }
  return context;
}
