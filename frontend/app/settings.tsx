import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Switch, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useAppSettings, AppSettings } from '../src/context/SettingsContext';
import { safeBack } from '../src/utils/navigation';

export default function SettingsScreen() {
  const router = useRouter();
  const { settings, colors, gradient, fontScale, updateSetting, playSound } = useAppSettings();
  const [saving, setSaving] = useState(false);

  const safeUpdate = async <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    try {
      setSaving(true);
      playSound('tap');
      await updateSetting(key, value);
      playSound('success');
    } catch (error) {
      playSound('error');
      Alert.alert('ERROR', 'Failed to save setting');
    } finally {
      setSaving(false);
    }
  };

  const cycleFontSize = () => {
    const sizes: AppSettings['font_size'][] = ['small', 'medium', 'large'];
    const next = sizes[(sizes.indexOf(settings.font_size) + 1) % sizes.length];
    safeUpdate('font_size', next);
  };

  const Row = ({ icon, color, label, desc, children }: any) => (
    <View style={[styles.settingRow, { backgroundColor: colors.surface, borderColor: colors.border }]}> 
      <View style={styles.settingLeft}>
        <View style={[styles.settingIcon, { backgroundColor: colors.card }]}> 
          <Ionicons name={icon} size={20} color={color} />
        </View>
        <View style={styles.settingTextWrap}>
          <Text style={[styles.settingLabel, { color: colors.text, fontSize: 9 * fontScale }]}>{label}</Text>
          <Text style={[styles.settingDesc, { color: colors.textMuted }]}>{desc}</Text>
        </View>
      </View>
      {children}
    </View>
  );

  return (
    <LinearGradient colors={gradient} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.header}>
          <TouchableOpacity style={[styles.backButton, { borderColor: colors.primary, backgroundColor: colors.surface }]} onPress={() => safeBack(router)}>
            <Ionicons name="arrow-back" size={24} color={colors.primary} />
          </TouchableOpacity>
          <Text style={[styles.title, { color: colors.primary, fontSize: 14 * fontScale }]}>SETTINGS</Text>
          <View style={{ width: 44 }} />
        </View>

        <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent}>
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.primary }]}>ACCESSIBILITY</Text>
            <Row icon="text" color={colors.info} label="FONT SIZE" desc="Tap to cycle small, medium, large">
              <TouchableOpacity style={[styles.fontSizeButton, { borderColor: colors.primary, backgroundColor: colors.card }]} onPress={cycleFontSize}>
                <Text style={[styles.fontSizeText, { color: colors.primary }]}>{settings.font_size.toUpperCase()}</Text>
              </TouchableOpacity>
            </Row>
            <Row icon="contrast" color={colors.warning} label="HIGH CONTRAST" desc="Maximum readability colors">
              <Switch value={settings.high_contrast} onValueChange={(v) => safeUpdate('high_contrast', v)} trackColor={{ false: '#777', true: colors.primary }} thumbColor={settings.high_contrast ? colors.warning : '#FFF'} />
            </Row>
            <Row icon="sunny" color={colors.warning} label="LIGHT MODE" desc="Switch full UI colors">
              <Switch value={settings.theme === 'light'} onValueChange={(v) => safeUpdate('theme', v ? 'light' : 'dark')} trackColor={{ false: '#777', true: colors.primary }} thumbColor="#FFF" />
            </Row>
            <Row icon="flash-off" color={colors.danger} label="REDUCED MOTION" desc="Minimize animations">
              <Switch value={settings.reduced_motion} onValueChange={(v) => safeUpdate('reduced_motion', v)} trackColor={{ false: '#777', true: colors.primary }} thumbColor="#FFF" />
            </Row>
          </View>

          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.primary }]}>SOUND + NOTIFICATIONS</Text>
            <Row icon="volume-high" color="#8A2BE2" label="SOUND EFFECTS" desc="Sleek tap/success/error sounds">
              <Switch value={settings.sound_effects} onValueChange={(v) => safeUpdate('sound_effects', v)} trackColor={{ false: '#777', true: colors.primary }} thumbColor="#FFF" />
            </Row>
            <Row icon="notifications" color={colors.primary} label="ALL EMAIL NOTIFICATIONS" desc="Master email notification switch">
              <Switch value={settings.notifications} onValueChange={(v) => safeUpdate('notifications', v)} trackColor={{ false: '#777', true: colors.primary }} thumbColor="#FFF" />
            </Row>
            <Row icon="log-in" color={colors.info} label="LOGIN EMAILS" desc="Email when someone logs in">
              <Switch value={settings.email_login} onValueChange={(v) => safeUpdate('email_login', v)} trackColor={{ false: '#777', true: colors.primary }} thumbColor="#FFF" />
            </Row>
            <Row icon="person-add" color={colors.primary} label="JOIN EMAILS" desc="Welcome emails after account creation">
              <Switch value={settings.email_join} onValueChange={(v) => safeUpdate('email_join', v)} trackColor={{ false: '#777', true: colors.primary }} thumbColor="#FFF" />
            </Row>
            <Row icon="star" color={colors.warning} label="VIP EMAILS" desc="VIP activation and perk notices">
              <Switch value={settings.email_vip} onValueChange={(v) => safeUpdate('email_vip', v)} trackColor={{ false: '#777', true: colors.primary }} thumbColor="#FFF" />
            </Row>
            <Row icon="alarm" color={colors.warning} label="DAILY REMINDERS" desc="Practice reminder emails">
              <Switch value={settings.daily_reminder && settings.email_daily} onValueChange={(v) => { safeUpdate('daily_reminder', v); safeUpdate('email_daily', v); }} trackColor={{ false: '#777', true: colors.primary }} thumbColor="#FFF" />
            </Row>
          </View>

          <View style={[styles.emailCard, { backgroundColor: colors.surface, borderColor: colors.border }]}> 
            <Text style={[styles.sectionTitle, { color: colors.primary }]}>BRANDED EMAILS</Text>
            <Text style={[styles.settingDesc, { color: colors.textMuted }]}>Codero sends polished game-style email cards with working buttons. Users can control what they receive here; templates are managed by the app owner only.</Text>
          </View>

          {saving && <Text style={[styles.savingText, { color: colors.primary }]}>SAVING...</Text>}
          <View style={styles.bottomPadding} />
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 20 },
  backButton: { width: 44, height: 44, borderRadius: 12, borderWidth: 0, justifyContent: 'center', alignItems: 'center' },
  title: { fontFamily: 'PressStart2P_400Regular' },
  scroll: { flex: 1 },
  scrollContent: { paddingHorizontal: 20, gap: 22 },
  section: { gap: 10 },
  sectionTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, marginBottom: 6 },
  settingRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderRadius: 12, padding: 14, borderWidth: 0, gap: 12, minHeight: 64 },
  settingLeft: { flexDirection: 'row', alignItems: 'center', flex: 1, gap: 12 },
  settingIcon: { width: 40, height: 40, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  settingTextWrap: { flex: 1, gap: 4 },
  settingLabel: { fontFamily: 'PressStart2P_400Regular' },
  settingDesc: { fontSize: 12, lineHeight: 17 },
  fontSizeButton: { paddingHorizontal: 12, paddingVertical: 10, borderRadius: 8, borderWidth: 0, minWidth: 90, alignItems: 'center' },
  fontSizeText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8 },
  emailCard: { borderRadius: 14, borderWidth: 0, padding: 16, gap: 12 },
  templateTabs: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  templateTab: { borderRadius: 999, paddingVertical: 9, paddingHorizontal: 10, backgroundColor: 'rgba(255,255,255,0.08)' },
  templateTabText: { fontFamily: 'PressStart2P_400Regular', fontSize: 7 },
  emailInput: { minHeight: 48, borderRadius: 10, borderWidth: 0, padding: 12, fontSize: 14 },
  emailBody: { minHeight: 150, textAlignVertical: 'top', lineHeight: 20 },
  emailButtons: { flexDirection: 'row', gap: 10 },
  emailButton: { flex: 1, minHeight: 48, borderRadius: 10, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 8 },
  emailButtonText: { fontFamily: 'PressStart2P_400Regular', fontSize: 7, textAlign: 'center' },
  savingText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, textAlign: 'center' },
  bottomPadding: { height: 40 },
});
