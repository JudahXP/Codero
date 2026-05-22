import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/services/api';
import { useAppSettings } from '../../src/context/SettingsContext';
import { safeBack } from '../../src/utils/navigation';

const GAMES = [
  { id: 'bug-hunter', name: 'BUG HUNTER', description: 'Find and fix bugs in real code.', icon: 'bug', colors: ['#FF6B6B', '#FF4757'] as const, xp: 'UP TO 30 XP', difficulty: 'MEDIUM' },
  { id: 'code-puzzle', name: 'CODE PUZZLE', description: 'Put scrambled code in order.', icon: 'extension-puzzle', colors: ['#00BFFF', '#0080FF'] as const, xp: 'UP TO 30 XP', difficulty: 'EASY' },
  { id: 'speed-code', name: 'SPEED CODE', description: 'Type code fast and build syntax muscle memory.', icon: 'flash', colors: ['#FFD700', '#FFA500'] as const, xp: 'UP TO 30 XP', difficulty: 'HARD' },
];

const LANGUAGES = [
  { id: 'python', name: 'Python', color: '#3776AB' }, { id: 'javascript', name: 'JavaScript', color: '#F7DF1E' }, { id: 'java', name: 'Java', color: '#ED8B00' }, { id: 'cpp', name: 'C++', color: '#00599C' },
  { id: 'csharp', name: 'C#', color: '#239120' }, { id: 'ruby', name: 'Ruby', color: '#CC342D' }, { id: 'go', name: 'Go', color: '#00ADD8' }, { id: 'rust', name: 'Rust', color: '#DEA584' },
  { id: 'swift', name: 'Swift', color: '#FA7343' }, { id: 'kotlin', name: 'Kotlin', color: '#7F52FF' }, { id: 'typescript', name: 'TypeScript', color: '#3178C6' }, { id: 'php', name: 'PHP', color: '#777BB4' },
  { id: 'sql', name: 'SQL', color: '#4479A1' }, { id: 'html_css', name: 'HTML/CSS', color: '#E34F26' }, { id: 'skript', name: 'Skript', color: '#6B8E23' }, { id: 'lua', name: 'Lua', color: '#000080' },
  { id: 'zig', name: 'Zig', color: '#F7A41D' }, { id: 'elixir', name: 'Elixir', color: '#4B275F' }, { id: 'shell', name: 'Shell', color: '#4EAA25' }, { id: 'haskell', name: 'Haskell', color: '#5D4F85' },
];

export default function GamesScreen() {
  const router = useRouter();
  const { colors, gradient, fontScale, playSound } = useAppSettings();
  const [stats, setStats] = useState<any>(null);
  const [selectedLang, setSelectedLang] = useState('python');

  useEffect(() => { fetchStats(); }, []);
  const fetchStats = async () => { try { const res = await api.get('/games/stats'); setStats(res.data); } catch (e) {} };
  const selectedLanguage = LANGUAGES.find((l) => l.id === selectedLang) || LANGUAGES[0];

  return (
    <LinearGradient colors={gradient} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.header}>
          <TouchableOpacity style={[styles.backButton, { borderColor: colors.primary, backgroundColor: colors.surface }]} onPress={() => safeBack(router)}>
            <Ionicons name="arrow-back" size={24} color={colors.primary} />
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: colors.primary, fontSize: 12 * fontScale }]}>CODING GAMES</Text>
          <View style={{ width: 44 }} />
        </View>

        {stats && stats.total_games > 0 && (
          <View style={styles.statsBar}><Ionicons name="game-controller" size={16} color={colors.primary} /><Text style={[styles.statValue, { color: colors.text }]}>{stats.total_games} PLAYED</Text></View>
        )}

        <View style={styles.languageHeader}>
          <Text style={[styles.languageTitle, { color: colors.text }]}>CHOOSE LANGUAGE</Text>
          <Text style={[styles.languageCount, { color: colors.primary }]}>{LANGUAGES.length} AVAILABLE</Text>
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.langScroll} contentContainerStyle={styles.langSelector}>
          {LANGUAGES.map((lang) => {
            const selected = selectedLang === lang.id;
            return (
              <TouchableOpacity key={lang.id} style={[styles.langChip, { backgroundColor: selected ? lang.color : colors.surface, borderColor: selected ? lang.color : colors.border }]} onPress={() => { playSound('tap'); setSelectedLang(lang.id); }}>
                <Text style={[styles.langChipText, { color: selected ? '#FFFFFF' : colors.text }]} numberOfLines={1}>{lang.name}</Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent}>
          <View style={[styles.selectedLanguageCard, { backgroundColor: colors.surface, borderColor: selectedLanguage.color }]}> 
            <Text style={[styles.selectedLanguageLabel, { color: colors.textMuted }]}>SELECTED</Text>
            <Text style={[styles.selectedLanguageName, { color: selectedLanguage.color }]}>{selectedLanguage.name.toUpperCase()}</Text>
          </View>

          {GAMES.map((game) => (
            <TouchableOpacity key={game.id} style={[styles.gameCard, { backgroundColor: colors.surface, borderColor: colors.border }]} activeOpacity={0.85} onPress={() => { playSound('tap'); router.push(`/games/${game.id}?lang=${selectedLang}`); }}>
              <LinearGradient colors={[...game.colors]} style={styles.gameIcon}><Ionicons name={game.icon as any} size={32} color="#FFF" /></LinearGradient>
              <View style={styles.gameInfo}>
                <Text style={[styles.gameName, { color: colors.text, fontSize: 10 * fontScale }]}>{game.name}</Text>
                <Text style={[styles.gameDesc, { color: colors.textMuted }]}>{game.description}</Text>
                <View style={styles.gameMetaRow}>
                  <View style={styles.gameMeta}><Ionicons name="star" size={12} color={colors.warning} /><Text style={[styles.gameMetaText, { color: colors.textMuted }]}>{game.xp}</Text></View>
                  <View style={styles.gameMeta}><Ionicons name="speedometer" size={12} color={colors.primary} /><Text style={[styles.gameMetaText, { color: colors.textMuted }]}>{game.difficulty}</Text></View>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={24} color={colors.primary} />
            </TouchableOpacity>
          ))}
          <View style={{ height: 40 }} />
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 20 },
  backButton: { width: 44, height: 44, borderRadius: 12, borderWidth: 1, justifyContent: 'center', alignItems: 'center' },
  headerTitle: { fontFamily: 'PressStart2P_400Regular' },
  statsBar: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 6, paddingHorizontal: 20, marginBottom: 12 },
  statValue: { fontFamily: 'PressStart2P_400Regular', fontSize: 8 },
  languageHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, marginBottom: 8 },
  languageTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 9 },
  languageCount: { fontFamily: 'PressStart2P_400Regular', fontSize: 7 },
  langScroll: { maxHeight: 52, marginBottom: 16 },
  langSelector: { paddingHorizontal: 20, gap: 8, alignItems: 'center' },
  langChip: { minWidth: 92, height: 42, paddingHorizontal: 12, borderRadius: 12, borderWidth: 1, justifyContent: 'center', alignItems: 'center' },
  langChipText: { fontSize: 13, fontWeight: '800', letterSpacing: 0.2 },
  scroll: { flex: 1 },
  scrollContent: { paddingHorizontal: 20, gap: 16 },
  selectedLanguageCard: { borderRadius: 14, borderWidth: 1, padding: 14, gap: 5 },
  selectedLanguageLabel: { fontFamily: 'PressStart2P_400Regular', fontSize: 7 },
  selectedLanguageName: { fontFamily: 'PressStart2P_400Regular', fontSize: 12 },
  gameCard: { flexDirection: 'row', alignItems: 'center', borderRadius: 16, padding: 16, borderWidth: 1, minHeight: 100 },
  gameIcon: { width: 64, height: 64, borderRadius: 16, justifyContent: 'center', alignItems: 'center' },
  gameInfo: { flex: 1, marginLeft: 16, gap: 6 },
  gameName: { fontFamily: 'PressStart2P_400Regular' },
  gameDesc: { fontSize: 13, lineHeight: 18 },
  gameMetaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 14 },
  gameMeta: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  gameMetaText: { fontFamily: 'PressStart2P_400Regular', fontSize: 6 },
});
