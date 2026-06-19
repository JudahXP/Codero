import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  BackHandler,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/services/api';
import { useAuth } from '../../src/context/AuthContext';
import { safeBack } from '../../src/utils/navigation';
import { useAppSettings } from '../../src/context/SettingsContext';
import * as Haptics from 'expo-haptics';

export default function CodePuzzleScreen() {
  const router = useRouter();
  const { lang } = useLocalSearchParams<{ lang: string }>();
  const { refreshUser } = useAuth();
  const { playSound } = useAppSettings();
  const language = lang || 'python';
  const [puzzles, setPuzzles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [current, setCurrent] = useState(0);
  const [selectedLines, setSelectedLines] = useState<number[]>([]);
  const [availableLines, setAvailableLines] = useState<number[]>([]);
  const [checked, setChecked] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [score, setScore] = useState(0);
  const [gameOver, setGameOver] = useState(false);
  const [gameResults, setGameResults] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleExit = useCallback(() => {
    if (gameOver) { safeBack(router, '/games'); return; }
    Alert.alert('QUIT GAME?', 'Your progress will be lost!', [
      { text: 'KEEP PLAYING', style: 'cancel' },
      { text: 'QUIT', style: 'destructive', onPress: () => safeBack(router, '/games') },
    ]);
  }, [gameOver, router]);

  useEffect(() => {
    const bh = BackHandler.addEventListener('hardwareBackPress', () => { handleExit(); return true; });
    return () => bh.remove();
  }, [handleExit]);

  useEffect(() => { fetchPuzzles(); }, [language]);

  const fetchPuzzles = async () => {
    try {
      const res = await api.get(`/games/code-puzzle/${language}`);
      setPuzzles(res.data.puzzles);
      if (res.data.puzzles.length > 0) {
        setAvailableLines(Array.from({ length: res.data.puzzles[0].lines.length }, (_, i) => i));
      }
    } catch (e) {
      Alert.alert('ERROR', 'Failed to load puzzles');
      safeBack(router, '/games');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectLine = (lineIdx: number) => {
    if (checked) return;
    setSelectedLines([...selectedLines, lineIdx]);
    setAvailableLines(availableLines.filter(i => i !== lineIdx));
  };

  const handleRemoveLine = (posIdx: number) => {
    if (checked) return;
    const lineIdx = selectedLines[posIdx];
    const newSelected = [...selectedLines];
    newSelected.splice(posIdx, 1);
    setSelectedLines(newSelected);
    setAvailableLines([...availableLines, lineIdx].sort((a, b) => a - b));
  };

  const handleCheck = async () => {
    if (selectedLines.length !== puzzles[current].lines.length) {
      Alert.alert('INCOMPLETE', 'Place all code lines in order!');
      return;
    }
    try {
      // Map selected indices back through original_indices
      const origIndices = puzzles[current].original_indices;
      const userOrder = selectedLines.map(i => origIndices[i]);
      const res = await api.post(`/games/code-puzzle/${language}/check`, {
        puzzle_id: puzzles[current].id,
        order: userOrder,
      });
      setResult(res.data);
      setChecked(true);
      if (res.data.correct) {
        setScore(s => s + 1);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      } else {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      }
    } catch (e) {
      Alert.alert('ERROR', 'Check failed');
    }
  };

  const handleNext = async () => {
    if (current < puzzles.length - 1) {
      const nextIdx = current + 1;
      setCurrent(nextIdx);
      setSelectedLines([]);
      setAvailableLines(Array.from({ length: puzzles[nextIdx].lines.length }, (_, i) => i));
      setChecked(false);
      setResult(null);
    } else {
      setSubmitting(true);
      try {
        const res = await api.post('/games/complete', {
          game_type: 'code_puzzle', score, total: puzzles.length, language,
        });
        setGameResults(res.data);
        setGameOver(true);
        await refreshUser();
      } catch (e) {
        setGameOver(true);
        setGameResults({ xp_earned: 0, score_pct: Math.round((score / puzzles.length) * 100) });
      } finally {
        setSubmitting(false);
      }
    }
  };

  if (loading) {
    return (
      <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
        <SafeAreaView style={styles.centered}>
          <ActivityIndicator size="large" color="#00BFFF" />
          <Text style={styles.loadingText}>SHUFFLING CODE...</Text>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  if (gameOver) {
    return (
      <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.resultsContainer}>
            <View style={styles.resultsIcon}>
              <Ionicons name="extension-puzzle" size={60} color="#00BFFF" />
            </View>
            <Text style={styles.resultsTitle}>
              {score >= puzzles.length ? 'PUZZLE MASTER!' : score >= 2 ? 'GREAT WORK!' : 'KEEP TRYING!'}
            </Text>
            <Text style={styles.resultsScore}>{score}/{puzzles.length} PUZZLES SOLVED</Text>
            {gameResults && (
              <View style={styles.resultsStats}>
                <View style={styles.resultsStat}>
                  <Ionicons name="star" size={20} color="#FFD700" />
                  <Text style={styles.resultsStatText}>+{gameResults.xp_earned} XP</Text>
                </View>
              </View>
            )}
            <TouchableOpacity style={styles.playAgainButton} onPress={() => {
              setCurrent(0); setScore(0); setSelectedLines([]); setChecked(false);
              setResult(null); setGameOver(false); setGameResults(null); setLoading(true); fetchPuzzles();
            }}>
              <Ionicons name="refresh" size={18} color="#00BFFF" />
              <Text style={styles.playAgainText}>PLAY AGAIN</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.backBtn} onPress={() => safeBack(router, '/games')}>
              <Text style={styles.backBtnText}>BACK TO GAMES</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  const puzzle = puzzles[current];

  return (
    <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.closeButton} onPress={handleExit}>
            <Ionicons name="close" size={24} color="#00BFFF" />
          </TouchableOpacity>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${((current + 1) / puzzles.length) * 100}%` }]} />
          </View>
          <Text style={styles.counterText}>{current + 1}/{puzzles.length}</Text>
        </View>

        <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent}>
          <View style={styles.conceptBadge}>
            <Ionicons name="school" size={14} color="#FFD700" />
            <Text style={styles.conceptText}>LEARNING: {puzzle.concept.toUpperCase()}</Text>
          </View>

          <Text style={styles.title}>{puzzle.title.toUpperCase()}</Text>
          <Text style={styles.desc}>{puzzle.description}</Text>

          {/* Your arrangement */}
          <Text style={styles.sectionLabel}>YOUR CODE ORDER:</Text>
          <View style={styles.arrangeBox}>
            {selectedLines.length === 0 ? (
              <Text style={styles.placeholderText}>TAP CODE LINES BELOW TO ARRANGE</Text>
            ) : (
              selectedLines.map((lineIdx, posIdx) => (
                <TouchableOpacity key={`sel-${posIdx}`} style={styles.selectedLine} onPress={() => handleRemoveLine(posIdx)}>
                  <Text style={styles.lineNumSmall}>{posIdx + 1}</Text>
                  <Text style={styles.selectedLineText}>{puzzle.lines[lineIdx]}</Text>
                  {!checked && <Ionicons name="close-circle" size={16} color="#FF6B6B" />}
                </TouchableOpacity>
              ))
            )}
          </View>

          {/* Available lines */}
          {availableLines.length > 0 && !checked && (
            <>
              <Text style={styles.sectionLabel}>AVAILABLE LINES:</Text>
              <View style={styles.availableBox}>
                {availableLines.map(lineIdx => (
                  <TouchableOpacity key={`avail-${lineIdx}`} style={styles.availableLine} onPress={() => handleSelectLine(lineIdx)}>
                    <Ionicons name="add-circle" size={16} color="#00BFFF" />
                    <Text style={styles.availableLineText}>{puzzle.lines[lineIdx]}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </>
          )}

          {checked && result && (
            <View style={[styles.feedbackBox, { borderColor: result.correct ? '#00FF88' : '#FF6B6B' }]}>
              <Ionicons name={result.correct ? 'checkmark-circle' : 'close-circle'} size={20} color={result.correct ? '#00FF88' : '#FF6B6B'} />
              <View style={{ flex: 1 }}>
                <Text style={[styles.feedbackTitle, { color: result.correct ? '#00FF88' : '#FF6B6B' }]}>
                  {result.correct ? 'PERFECT ORDER!' : 'NOT QUITE RIGHT'}
                </Text>
                <Text style={styles.feedbackExpl}>{result.explanation}</Text>
                {!result.correct && result.correct_lines && (
                  <View style={styles.correctOrderBox}>
                    <Text style={styles.correctOrderLabel}>CORRECT ORDER:</Text>
                    {result.correct_lines.map((line: string, i: number) => (
                      <Text key={i} style={styles.correctOrderLine}>{i + 1}. {line}</Text>
                    ))}
                  </View>
                )}
              </View>
            </View>
          )}
        </ScrollView>

        <View style={styles.footer}>
          {!checked ? (
            <TouchableOpacity style={styles.checkBtn} onPress={handleCheck}>
              <LinearGradient colors={['#00BFFF', '#0080FF']} style={styles.checkGrad}>
                <Ionicons name="checkmark" size={20} color="#FFF" />
                <Text style={styles.checkBtnText}>CHECK ORDER</Text>
              </LinearGradient>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity style={styles.nextBtn} onPress={handleNext} disabled={submitting}>
              <LinearGradient colors={['#00FF88', '#00CC6A']} style={styles.nextGrad}>
                {submitting ? <ActivityIndicator color="#0D0D0D" /> : (
                  <Text style={styles.nextBtnText}>{current < puzzles.length - 1 ? 'NEXT PUZZLE' : 'SEE RESULTS'}</Text>
                )}
              </LinearGradient>
            </TouchableOpacity>
          )}
        </View>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#00BFFF', marginTop: 16 },
  header: { flexDirection: 'row', alignItems: 'center', padding: 16, gap: 12 },
  closeButton: {
    width: 40, height: 40, borderRadius: 10,
    backgroundColor: 'rgba(0,191,255,0.1)', justifyContent: 'center', alignItems: 'center',
  },
  progressBar: { flex: 1, height: 8, backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 4, overflow: 'hidden' },
  progressFill: { height: '100%', backgroundColor: '#00BFFF', borderRadius: 4 },
  counterText: { fontFamily: 'PressStart2P_400Regular', fontSize: 9, color: '#00BFFF' },
  scroll: { flex: 1 },
  scrollContent: { padding: 16 },
  conceptBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: 'rgba(255,215,0,0.1)', borderRadius: 8,
    paddingHorizontal: 10, paddingVertical: 6, alignSelf: 'flex-start', marginBottom: 12,
  },
  conceptText: { fontFamily: 'PressStart2P_400Regular', fontSize: 6, color: '#FFD700' },
  title: { fontFamily: 'PressStart2P_400Regular', fontSize: 14, color: '#00BFFF', marginBottom: 8 },
  desc: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#888', marginBottom: 20, lineHeight: 16 },
  sectionLabel: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#FFF', marginBottom: 10, marginTop: 8 },
  arrangeBox: {
    backgroundColor: 'rgba(0,191,255,0.05)', borderRadius: 12, padding: 12,
    borderWidth: 0, borderColor: 'rgba(0,191,255,0.2)', borderStyle: 'dashed', minHeight: 60, marginBottom: 16,
  },
  placeholderText: { fontFamily: 'PressStart2P_400Regular', fontSize: 7, color: '#555', textAlign: 'center', paddingVertical: 16 },
  selectedLine: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: 'rgba(0,191,255,0.1)', borderRadius: 8, padding: 10, marginBottom: 6,
    borderWidth: 0, borderColor: 'rgba(0,191,255,0.3)',
  },
  lineNumSmall: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#00BFFF', width: 20 },
  selectedLineText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#00BFFF', flex: 1 },
  availableBox: { gap: 6 },
  availableLine: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 8, padding: 10,
    borderWidth: 0, borderColor: 'rgba(255,255,255,0.1)',
  },
  availableLineText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#CCC', flex: 1 },
  feedbackBox: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 12,
    borderRadius: 12, padding: 14, marginTop: 16, borderWidth: 0,
    backgroundColor: 'rgba(255,255,255,0.02)',
  },
  feedbackTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, marginBottom: 6 },
  feedbackExpl: { fontFamily: 'PressStart2P_400Regular', fontSize: 7, color: '#CCC', lineHeight: 14 },
  correctOrderBox: { backgroundColor: 'rgba(0,255,136,0.1)', borderRadius: 8, padding: 10, marginTop: 10 },
  correctOrderLabel: { fontFamily: 'PressStart2P_400Regular', fontSize: 7, color: '#00FF88', marginBottom: 6 },
  correctOrderLine: { fontFamily: 'PressStart2P_400Regular', fontSize: 7, color: '#00FF88', marginBottom: 3 },
  footer: { padding: 16 },
  checkBtn: { borderRadius: 12, overflow: 'hidden' },
  checkGrad: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 16, gap: 10 },
  checkBtnText: { fontFamily: 'PressStart2P_400Regular', fontSize: 12, color: '#FFF' },
  nextBtn: { borderRadius: 12, overflow: 'hidden' },
  nextGrad: { alignItems: 'center', justifyContent: 'center', paddingVertical: 16 },
  nextBtnText: { fontFamily: 'PressStart2P_400Regular', fontSize: 12, color: '#0D0D0D' },
  resultsContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  resultsIcon: {
    width: 120, height: 120, borderRadius: 60,
    backgroundColor: 'rgba(0,191,255,0.1)', justifyContent: 'center', alignItems: 'center', marginBottom: 24,
  },
  resultsTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 16, color: '#00BFFF', marginBottom: 12, textAlign: 'center' },
  resultsScore: { fontFamily: 'PressStart2P_400Regular', fontSize: 14, color: '#FFF', marginBottom: 24 },
  resultsStats: { flexDirection: 'row', gap: 24, marginBottom: 32 },
  resultsStat: { alignItems: 'center', gap: 6 },
  resultsStatText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#FFF' },
  playAgainButton: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: 'rgba(0,191,255,0.1)', borderWidth: 0, borderColor: '#00BFFF',
    borderRadius: 12, paddingVertical: 14, paddingHorizontal: 24, marginBottom: 12,
  },
  playAgainText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#00BFFF' },
  backBtn: { paddingVertical: 12 },
  backBtnText: { fontFamily: 'PressStart2P_400Regular', fontSize: 9, color: '#888' },
});
