import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../services/api';

interface User {
  id: string;
  username: string;
  email: string;
  xp: number;
  level: number;
  streak: number;
  hearts: number;
  gems?: number;
  badges: string[];
  friends: string[];
  settings?: {
    font_size?: 'small' | 'medium' | 'large';
    high_contrast?: boolean;
    reduced_motion?: boolean;
    sound_effects?: boolean;
    notifications?: boolean;
    daily_reminder?: boolean;
    email_login?: boolean;
    email_join?: boolean;
    email_vip?: boolean;
    email_daily?: boolean;
    theme?: 'dark' | 'light';
  };
  email_verified?: boolean;
  is_admin?: boolean;
  admin_tag?: string | null;

  profile?: {
    display_name?: string;
    bio?: string;
    avatar_color?: string;
    display_badges?: string[];
  };
  auth_methods?: {
    password?: boolean;
    email_verified?: boolean;
    passkey_ready?: boolean;
    google_ready?: boolean;
  };
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  updateLocalUser: (updates: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      if (token) {
        const response = await api.get('/auth/me');
        setUser(response.data);
      }
    } catch (error) {
      await AsyncStorage.removeItem('token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    await AsyncStorage.setItem('token', response.data.token);
    setUser(response.data.user);
  };

  const register = async (username: string, email: string, password: string) => {
    const response = await api.post('/auth/register', { username, email, password });
    await AsyncStorage.setItem('token', response.data.token);
    setUser(response.data.user);
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      // Ignore logout errors
    }
    await AsyncStorage.removeItem('token');
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const response = await api.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  };

  const updateLocalUser = (updates: Partial<User>) => {
    if (user) {
      setUser({ ...user, ...updates });
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser, updateLocalUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
