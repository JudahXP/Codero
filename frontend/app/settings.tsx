import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Switch,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context'
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../src/context/AuthContext';
import { api } from '../src/services/api';

interface Settings {
  font_size: 'small' | 'medium' | 'large';
  high_contrast: boolean;
  reduced_motion: boolean;
  sound_effects: boolean;
  notifications: boolean;
  daily_reminder: boolean;
  theme: 'dark' | 'light';
}

export default function SettingsScreen() {
  const router = useRouter();
  const { user, refreshUser } = useAuth();
  const [settings, setSettings] = useState<Settings>({
    font_size: 'medium',
    high_contrast: false,
    reduced_motion: false,
    sound_effects: true,
    notifications: true,
    daily_reminder: true,
    theme: 'dark',
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (user?.settings) {
      setSettings({ ...settings, ...user.settings });
    }
  }, [user]);

  const updateSetting = async (key: keyof Settings, value: any) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);

    try {
      setSaving(true);
      await api.put('/settings', { settings: newSettings });
      await refreshUser();
    } catch (error) {
      console.error('Failed to save settings:', error);
      Alert.alert('ERROR', 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const fontSizeLabel = {
    small: 'SMALL',
    medium: 'MEDIUM',
    large: 'LARGE',
  };

  const cycleFontSize = () => {
    const sizes: Array<'small' | 'medium' | 'large'> = ['small', 'medium', 'large'];
    const currentIndex = sizes.indexOf(settings.font_size);
    const nextIndex = (currentIndex + 1) % sizes.length;
    updateSetting('font_size', sizes[nextIndex]);
  };

  return (
    <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={24} color="#00FF88" />
          </TouchableOpacity>
          <Text style={styles.title}>SETTINGS</Text>
          <View style={{ width: 44 }} />
        </View>

        <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent}>
          {/* Accessibility Section */}
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="accessibility" size={20} color="#00FF88" />
              <Text style={styles.sectionTitle}>ACCESSIBILITY</Text>
            </View>

            {/* Font Size */}
            <TouchableOpacity style={styles.settingRow} onPress={cycleFontSize}>
              <View style={styles.settingLeft}>
                <View style={[styles.settingIcon, { backgroundColor: 'rgba(0, 191, 255, 0.1)' }]}>
                  <Ionicons name="text" size={20} color="#00BFFF" />
                </View>
                <View>
                  <Text style={styles.settingLabel}>FONT SIZE</Text>
                  <Text style={styles.settingDesc}>Adjust text size</Text>
                </View>
              </View>
              <View style={styles.fontSizeButton}>
                <Text style={styles.fontSizeText}>{fontSizeLabel[settings.font_size]}</Text>
              </View>
            </TouchableOpacity>

            {/* High Contrast */}
            <View style={styles.settingRow}>
              <View style={styles.settingLeft}>
                <View style={[styles.settingIcon, { backgroundColor: 'rgba(255, 215, 0, 0.1)' }]}>
                  <Ionicons name="contrast" size={20} color="#FFD700" />
                </View>
                <View>
                  <Text style={styles.settingLabel}>HIGH CONTRAST</Text>
                  <Text style={styles.settingDesc}>Increase color contrast</Text>
                </View>
              </View>
              <Switch
                value={settings.high_contrast}
                onValueChange={(value) => updateSetting('high_contrast', value)}
                trackColor={{ false: '#333', true: '#00FF88' }}
                thumbColor={settings.high_contrast ? '#FFF' : '#888'}
              />
            </View>

            {/* Reduced Motion */}
            <View style={styles.settingRow}>
              <View style={styles.settingLeft}>
                <View style={[styles.settingIcon, { backgroundColor: 'rgba(255, 107, 107, 0.1)' }]}>
                  <Ionicons name="flash-off" size={20} color="#FF6B6B" />
                </View>
                <View>
                  <Text style={styles.settingLabel}>REDUCED MOTION</Text>
                  <Text style={styles.settingDesc}>Minimize animations</Text>
                </View>
              </View>
              <Switch
                value={settings.reduced_motion}
                onValueChange={(value) => updateSetting('reduced_motion', value)}
                trackColor={{ false: '#333', true: '#00FF88' }}
                thumbColor={settings.reduced_motion ? '#FFF' : '#888'}
              />
            </View>
          </View>

          {/* Sound & Notifications Section */}
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="notifications" size={20} color="#00FF88" />
              <Text style={styles.sectionTitle}>NOTIFICATIONS</Text>
            </View>

            {/* Sound Effects */}
            <View style={styles.settingRow}>
              <View style={styles.settingLeft}>
                <View style={[styles.settingIcon, { backgroundColor: 'rgba(138, 43, 226, 0.1)' }]}>
                  <Ionicons name="volume-high" size={20} color="#8A2BE2" />
                </View>
                <View>
                  <Text style={styles.settingLabel}>SOUND EFFECTS</Text>
                  <Text style={styles.settingDesc}>Play audio feedback</Text>
                </View>
              </View>
              <Switch
                value={settings.sound_effects}
                onValueChange={(value) => updateSetting('sound_effects', value)}
                trackColor={{ false: '#333', true: '#00FF88' }}
                thumbColor={settings.sound_effects ? '#FFF' : '#888'}
              />
            </View>

            {/* Push Notifications */}
            <View style={styles.settingRow}>
              <View style={styles.settingLeft}>
                <View style={[styles.settingIcon, { backgroundColor: 'rgba(0, 255, 136, 0.1)' }]}>
                  <Ionicons name="notifications" size={20} color="#00FF88" />
                </View>
                <View>
                  <Text style={styles.settingLabel}>NOTIFICATIONS</Text>
                  <Text style={styles.settingDesc}>Push notifications</Text>
                </View>
              </View>
              <Switch
                value={settings.notifications}
                onValueChange={(value) => updateSetting('notifications', value)}
                trackColor={{ false: '#333', true: '#00FF88' }}
                thumbColor={settings.notifications ? '#FFF' : '#888'}
              />
            </View>

            {/* Daily Reminder */}
            <View style={styles.settingRow}>
              <View style={styles.settingLeft}>
                <View style={[styles.settingIcon, { backgroundColor: 'rgba(255, 165, 0, 0.1)' }]}>
                  <Ionicons name="alarm" size={20} color="#FFA500" />
                </View>
                <View>
                  <Text style={styles.settingLabel}>DAILY REMINDER</Text>
                  <Text style={styles.settingDesc}>Practice reminder</Text>
                </View>
              </View>
              <Switch
                value={settings.daily_reminder}
                onValueChange={(value) => updateSetting('daily_reminder', value)}
                trackColor={{ false: '#333', true: '#00FF88' }}
                thumbColor={settings.daily_reminder ? '#FFF' : '#888'}
              />
            </View>
          </View>

          {/* About Section */}
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="information-circle" size={20} color="#00FF88" />
              <Text style={styles.sectionTitle}>ABOUT</Text>
            </View>

            <View style={styles.aboutCard}>
              <Text style={styles.appName}>CODERO</Text>
              <Text style={styles.appVersion}>VERSION 2.0</Text>
              <Text style={styles.appDesc}>LEARN TO CODE LIKE A GAME</Text>
            </View>

            <View style={styles.statsRow}>
              <View style={styles.statBox}>
                <Ionicons name="language" size={24} color="#00BFFF" />
                <Text style={styles.statValue}>20</Text>
                <Text style={styles.statLabel}>LANGUAGES</Text>
              </View>
              <View style={styles.statBox}>
                <Ionicons name="book" size={24} color="#FFD700" />
                <Text style={styles.statValue}>600+</Text>
                <Text style={styles.statLabel}>LESSONS</Text>
              </View>
              <View style={styles.statBox}>
                <Ionicons name="help-circle" size={24} color="#FF6B6B" />
                <Text style={styles.statValue}>6000+</Text>
                <Text style={styles.statLabel}>EXERCISES</Text>
              </View>
            </View>
          </View>

          {saving && (
            <Text style={styles.savingText}>SAVING...</Text>
          )}

          <View style={styles.bottomPadding} />
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 20,
  },
  backButton: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: 'rgba(0, 255, 136, 0.1)',
    borderWidth: 1,
    borderColor: '#00FF88',
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 14,
    color: '#00FF88',
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 16,
  },
  sectionTitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#00FF88',
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingIcon: {
    width: 40,
    height: 40,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  settingLabel: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#FFF',
  },
  settingDesc: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 6,
    color: '#888',
    marginTop: 2,
  },
  fontSizeButton: {
    backgroundColor: 'rgba(0, 255, 136, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#00FF88',
  },
  fontSizeText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#00FF88',
  },
  aboutCard: {
    backgroundColor: 'rgba(0, 255, 136, 0.1)',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(0, 255, 136, 0.3)',
    marginBottom: 16,
  },
  appName: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 20,
    color: '#00FF88',
    marginBottom: 8,
  },
  appVersion: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#888',
    marginBottom: 4,
  },
  appDesc: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 7,
    color: '#AAA',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 10,
  },
  statBox: {
    flex: 1,
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  statValue: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 14,
    color: '#FFF',
    marginVertical: 6,
  },
  statLabel: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 6,
    color: '#888',
  },
  savingText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#00FF88',
    textAlign: 'center',
    marginTop: 10,
  },
  bottomPadding: {
    height: 40,
  },
});
