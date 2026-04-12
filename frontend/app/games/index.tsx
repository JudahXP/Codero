import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/services/api';

const GAMES = [
  {
    id: 'bug-hunter',
    name: 'BUG HUNTER',
    description: 'Find & fix bugs in real code. Learn debugging skills!',
    icon: 'bug',
    colors: ['#FF6B6B', '#FF4757'] as const,
    xp: 'UP TO 30 XP',
    difficulty: 'MEDIUM',
  },
  {
    id: 'code-puzzle',
    name: 'CODE PUZZLE',
    description: 'Put scrambled code in order. Master code structure!',
    icon: 'extension-puzzle',
    colors: ['#00BFFF', '#0080FF'] as const,
    xp: 'UP TO 30 XP',
    difficulty: 'EASY',
  },
  {
    id: 'speed-code',
    name: 'SPEED CODE',
    description: 'Type code fast! Build muscle memory for syntax.',
    icon: 'flash',
    colors: ['#FFD700', '#FFA500'] as const,
    xp: 'UP TO 30 XP',
    difficulty: 'HARD',
  },
];

const LANGUAGES = [
  { id: 'python', name: 'PYTHON', color: '#3776AB' },
  { id: 'javascript', name: 'JS', color: '#F7DF1E' },
  { id: 'shell', name: 'SHELL', color: '#4EAA25' },
  { id: 'lua', name: 'LUA', color: '#000080' },
  { id: 'haskell', name: 'HASKELL', color: '#5D4F85' },
  { id: 'elixir', name: 'ELIXIR', color: '#4B275F' },
  { id: 'zig', name: 'ZIG', color: '#F7A41D' },
  { id: 'skript', name: 'SKRIPT', color: '#6B8E23' },
];

export default function GamesScreen() {
  const router = useRouter();
  const [stats, setStats] = useState<any>(null);
  const [selectedLang, setSelectedLang] = useState('python');

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await api.get('/games/stats');
      setStats(res.data);
    } catch (e) {
      // ignore
    }
  };

  return (
    <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={24} color="#00FF88" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>CODING GAMES</Text>
          <View style={{ width: 44 }} />
        </View>

        {stats && stats.total_games > 0 && (
          <View style={styles.statsBar}>
            <View style={styles.statItem}>
              <Ionicons name="game-controller" size={16} color="#00FF88" />
              <Text style={styles.statValue}>{stats.total_games} PLAYED</Text>
            </View>
          </View>
        )}

        {/* Language Selector */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.langScroll} contentContainerStyle={styles.langSelector}>
          {LANGUAGES.map(lang => (
            <TouchableOpacity
              key={lang.id}
              style={[
                styles.langChip,
                selectedLang === lang.id && { backgroundColor: lang.color + '30', borderColor: lang.color },
              ]}
              onPress={() => setSelectedLang(lang.id)}
            >
              <Text style={[
                styles.langChipText,
                selectedLang === lang.id && { color: lang.color },
              ]}>{lang.name}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent}>
          {GAMES.map(game => (
            <TouchableOpacity
              key={game.id}
              style={styles.gameCard}
              activeOpacity={0.8}
              onPress={() => router.push(`/games/${game.id}?lang=${selectedLang}`)}
            >
              <LinearGradient
                colors={[...game.colors]}
                style={styles.gameIcon}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Ionicons name={game.icon as any} size={32} color="#FFF" />
              </LinearGradient>
              <View style={styles.gameInfo}>
                <Text style={styles.gameName}>{game.name}</Text>
                <Text style={styles.gameDesc}>{game.description}</Text>
                <View style={styles.gameMetaRow}>
                  <View style={styles.gameMeta}>
                    <Ionicons name="star" size={12} color="#FFD700" />
                    <Text style={styles.gameMetaText}>{game.xp}</Text>
                  </View>
                  <View style={styles.gameMeta}>
                    <Ionicons name="speedometer" size={12} color="#00FF88" />
                    <Text style={styles.gameMetaText}>{game.difficulty}</Text>
                  </View>
                </View>
              </View>
              <Ionicons name="chevron-forward" size={24} color="#00FF88" />
            </TouchableOpacity>
          ))}

          {/* Learning Tips */}
          <View style={styles.tipsSection}>
            <Text style={styles.tipsTitle}>WHY PLAY GAMES?</Text>
            <View style={styles.tipCard}>
              <Ionicons name="bulb" size={20} color="#FFD700" />
              <Text style={styles.tipText}>Bug Hunter teaches you to spot common mistakes before they happen in your real code</Text>
            </View>
            <View style={styles.tipCard}>
              <Ionicons name="layers" size={20} color="#00BFFF" />
              <Text style={styles.tipText}>Code Puzzle builds understanding of how code flows from top to bottom</Text>
            </View>
            <View style={styles.tipCard}>
              <Ionicons name="flash" size={20} color="#FFD700" />
              <Text style={styles.tipText}>Speed Code creates muscle memory so you can write code without thinking about syntax</Text>
            </View>
          </View>
          <View style={{ height: 40 }} />
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 20,
  },
  backButton: {
    width: 44, height: 44, borderRadius: 12,
    backgroundColor: 'rgba(0, 255, 136, 0.1)', borderWidth: 1, borderColor: '#00FF88',
    justifyContent: 'center', alignItems: 'center',
  },
  headerTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 12, color: '#00FF88' },
  statsBar: {
    flexDirection: 'row', justifyContent: 'center', paddingHorizontal: 20, marginBottom: 12,
  },
  statItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  statValue: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#FFF' },
  langScroll: {
    maxHeight: 44, marginBottom: 16,
  },
  langSelector: {
    paddingHorizontal: 20, gap: 8,
  },
  langChip: {
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 8,
    backgroundColor: 'rgba(255,255,255,0.05)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)',
  },
  langChipText: { fontFamily: 'PressStart2P_400Regular', fontSize: 7, color: '#888' },
  scroll: { flex: 1 },
  scrollContent: { paddingHorizontal: 20, gap: 16 },
  gameCard: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 16, padding: 16,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)',
  },
  gameIcon: {
    width: 64, height: 64, borderRadius: 16,
    justifyContent: 'center', alignItems: 'center',
  },
  gameInfo: { flex: 1, marginLeft: 16 },
  gameName: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#FFF', marginBottom: 6 },
  gameDesc: { fontFamily: 'PressStart2P_400Regular', fontSize: 6, color: '#888', lineHeight: 12, marginBottom: 8 },
  gameMetaRow: { flexDirection: 'row', gap: 16 },
  gameMeta: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  gameMetaText: { fontFamily: 'PressStart2P_400Regular', fontSize: 6, color: '#AAA' },
  tipsSection: { marginTop: 16 },
  tipsTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#FFD700', marginBottom: 12 },
  tipCard: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 12,
    backgroundColor: 'rgba(255,215,0,0.05)', borderRadius: 10, padding: 12, marginBottom: 8,
    borderWidth: 1, borderColor: 'rgba(255,215,0,0.1)',
  },
  tipText: { fontFamily: 'PressStart2P_400Regular', fontSize: 7, color: '#CCC', flex: 1, lineHeight: 14 },
});
