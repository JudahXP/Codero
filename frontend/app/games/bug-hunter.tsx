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

interface Challenge {
  id: string;
  code: string;
  question: string;
  options: string[];
  concept: string;
}

export default function BugHunterScreen() {
  const router = useRouter();
  const { lang } = useLocalSearchParams<{ lang: string }>();
  const { refreshUser } = useAuth();
  const { playSound } = useAppSettings();
  const language = lang || 'python';
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [loading, setLoading] = useState(true);
  const [current, setCurrent] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [checked, setChecked] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [score, setScore] = useState(0);
  const [gameOver, setGameOver] = useState(false);
  const [gameResults, setGameResults] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);

  // Exit confirmation - back handler
  const handleExit = useCallback(() => {
    if (gameOver) {
      safeBack(router, '/games');
      return;
    }
    Alert.alert(
      'QUIT GAME?',
      'Your progress will be lost!',
      [
        { text: 'KEEP PLAYING', style: 'cancel' },
        { text: 'QUIT', style: 'destructive', onPress: () => safeBack(router, '/games') },
      ]
    );
  }, [gameOver, router]);

  useEffect(() => {
    const backHandler = BackHandler.addEventListener('hardwareBackPress', () => {
      handleExit();
      return true;
    });
    return () => backHandler.remove();
  }, [handleExit]);

  useEffect(() => {
    fetchChallenges();
  }, [language]);

  const fetchChallenges = async () => {
    try {
      const res = await api.get(`/games/bug-hunter/${language}`);
      setChallenges(res.data.challenges);
    } catch (e) {
      Alert.alert('ERROR', 'Failed to load game');
      safeBack(router, '/games');
    } finally {
      setLoading(false);
    }
  };

  const handleCheck = async () => {
    if (selected === null) {
      Alert.alert('SELECT', 'Pick an answer first!');
      return;
    }
    try {
      const res = await api.post(`/games/bug-hunter/${language}/check`, {
        challenge_id: challenges[current].id,
        selected,
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
    if (current < challenges.length - 1) {
      setCurrent(c => c + 1);
      setSelected(null);
      setChecked(false);
      setResult(null);
    } else {
      // Game over - submit
      setSubmitting(true);
      try {
        const res = await api.post('/games/complete', {
          game_type: 'bug_hunter',
          score,
          total: challenges.length,
          language,
        });
        setGameResults(res.data);
        setGameOver(true);
        await refreshUser();
      } catch (e) {
        setGameOver(true);
        setGameResults({ xp_earned: 0, score_pct: Math.round((score / challenges.length) * 100) });
      } finally {
        setSubmitting(false);
      }
    }
  };

  if (loading) {
    return (
      <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
        <SafeAreaView style={styles.centered}>
          <ActivityIndicator size="large" color="#FF6B6B" />
          <Text style={styles.loadingText}>FINDING BUGS...</Text>
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
              <Ionicons name={score >= 3 ? 'bug' : 'sad'} size={60} color="#FF6B6B" />
            </View>
            <Text style={styles.resultsTitle}>
              {score >= 4 ? 'BUG EXTERMINATOR!' : score >= 3 ? 'NICE DEBUGGING!' : 'KEEP LEARNING!'}
            </Text>
            <Text style={styles.resultsScore}>{score}/{challenges.length} BUGS FOUND</Text>
            {gameResults && (
              <View style={styles.resultsStats}>
                <View style={styles.resultsStat}>
                  <Ionicons name="star" size={20} color="#FFD700" />
                  <Text style={styles.resultsStatText}>+{gameResults.xp_earned} XP</Text>
                </View>
                {gameResults.gems_earned > 0 && (
                  <View style={styles.resultsStat}>
                    <Ionicons name="diamond" size={20} color="#00BFFF" />
                    <Text style={styles.resultsStatText}>+{gameResults.gems_earned} GEMS</Text>
                  </View>
                )}
              </View>
            )}
            <TouchableOpacity style={styles.playAgainButton} onPress={() => {
              setCurrent(0); setScore(0); setSelected(null); setChecked(false);
              setResult(null); setGameOver(false); setGameResults(null); setLoading(true); fetchChallenges();
            }}>
              <Ionicons name="refresh" size={18} color="#FF6B6B" />
              <Text style={styles.playAgainText}>PLAY AGAIN</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.backToGamesButton} onPress={() => safeBack(router, '/games')}>
              <Text style={styles.backToGamesText}>BACK TO GAMES</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  const challenge = challenges[current];

  return (
    <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.closeButton} onPress={handleExit}>
            <Ionicons name="close" size={24} color="#FF6B6B" />
          </TouchableOpacity>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${((current + 1) / challenges.length) * 100}%` }]} />
          </View>
          <Text style={styles.scoreText}>{score}/{current + 1}</Text>
        </View>

        <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent}>
          {/* Concept badge */}
          <View style={styles.conceptBadge}>
            <Ionicons name="school" size={14} color="#FFD700" />
            <Text style={styles.conceptText}>LEARNING: {challenge.concept.toUpperCase()}</Text>
          </View>

          <Text style={styles.question}>{challenge.question}</Text>

          {/* Code Display */}
          <View style={styles.codeBlock}>
            {challenge.code.split('\n').map((line, i) => (
              <View key={i} style={styles.codeLine}>
                <Text style={styles.lineNum}>{i + 1}</Text>
                <Text style={styles.codeText}>{line}</Text>
              </View>
            ))}
          </View>

          {/* Options */}
          <View style={styles.optionsContainer}>
            {challenge.options.map((opt, i) => {
              let borderCol = 'rgba(255,255,255,0.1)';
              let bgCol = 'rgba(255,255,255,0.05)';
              if (checked && result) {
                if (i === result.correct_answer) { borderCol = '#00FF88'; bgCol = 'rgba(0,255,136,0.1)'; }
                else if (i === selected && !result.correct) { borderCol = '#FF6B6B'; bgCol = 'rgba(255,107,107,0.1)'; }
              } else if (selected === i) {
                borderCol = '#FF6B6B'; bgCol = 'rgba(255,107,107,0.1)';
              }
              return (
                <TouchableOpacity
                  key={i}
                  style={[styles.optionButton, { borderColor: borderCol, backgroundColor: bgCol }]}
                  onPress={() => {
                    if (!checked) {
                      setSelected(i);
                      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                    }
                  }}
                  disabled={checked}
                >
                  <Text style={styles.optionText}>{opt}</Text>
                </TouchableOpacity>
              );
            })}
          </View>

          {/* Result feedback */}
          {checked && result && (
            <View style={[styles.feedbackBox, { borderColor: result.correct ? '#00FF88' : '#FF6B6B' }]}>
              <Ionicons name={result.correct ? 'checkmark-circle' : 'close-circle'} size={20} color={result.correct ? '#00FF88' : '#FF6B6B'} />
              <View style={{ flex: 1 }}>
                <Text style={[styles.feedbackTitle, { color: result.correct ? '#00FF88' : '#FF6B6B' }]}>
                  {result.correct ? 'CORRECT!' : 'NOT QUITE!'}
                </Text>
                <Text style={styles.feedbackExplanation}>{result.explanation}</Text>
                {result.fixed_code && (
                  <View style={styles.fixedCodeBox}>
                    <Text style={styles.fixedCodeLabel}>FIXED CODE:</Text>
                    <Text style={styles.fixedCodeText}>{result.fixed_code}</Text>
                  </View>
                )}
              </View>
            </View>
          )}
        </ScrollView>

        <View style={styles.footer}>
          {!checked ? (
            <TouchableOpacity style={styles.checkButton} onPress={handleCheck}>
              <LinearGradient colors={['#FF6B6B', '#FF4757']} style={styles.checkGradient}>
                <Ionicons name="bug" size={20} color="#FFF" />
                <Text style={styles.checkText}>CHECK BUG</Text>
              </LinearGradient>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity style={styles.nextButton} onPress={handleNext} disabled={submitting}>
              <LinearGradient colors={['#00FF88', '#00CC6A']} style={styles.nextGradient}>
                {submitting ? <ActivityIndicator color="#0D0D0D" /> : (
                  <Text style={styles.nextText}>
                    {current < challenges.length - 1 ? 'NEXT BUG' : 'SEE RESULTS'}
                  </Text>
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
  loadingText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#FF6B6B', marginTop: 16 },
  header: { flexDirection: 'row', alignItems: 'center', padding: 16, gap: 12 },
  closeButton: {
    width: 40, height: 40, borderRadius: 10,
    backgroundColor: 'rgba(255,107,107,0.1)', justifyContent: 'center', alignItems: 'center',
  },
  progressBar: { flex: 1, height: 8, backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 4, overflow: 'hidden' },
  progressFill: { height: '100%', backgroundColor: '#FF6B6B', borderRadius: 4 },
  scoreText: { fontFamily: 'PressStart2P_400Regular', fontSize: 9, color: '#FF6B6B' },
  scroll: { flex: 1 },
  scrollContent: { padding: 16 },
  conceptBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: 'rgba(255,215,0,0.1)', borderRadius: 8,
    paddingHorizontal: 10, paddingVertical: 6, alignSelf: 'flex-start', marginBottom: 16,
  },
  conceptText: { fontFamily: 'PressStart2P_400Regular', fontSize: 6, color: '#FFD700' },
  question: { fontFamily: 'PressStart2P_400Regular', fontSize: 11, color: '#FFF', lineHeight: 20, marginBottom: 16 },
  codeBlock: {
    backgroundColor: '#1a1a1a', borderRadius: 12, padding: 14, borderWidth: 0, borderColor: '#333', marginBottom: 20,
  },
  codeLine: { flexDirection: 'row', marginBottom: 4 },
  lineNum: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#555', width: 24 },
  codeText: { fontFamily: 'PressStart2P_400Regular', fontSize: 9, color: '#FF6B6B' },
  optionsContainer: { gap: 10 },
  optionButton: {
    borderRadius: 12, padding: 14, borderWidth: 0,
  },
  optionText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#DDD' },
  feedbackBox: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 12,
    borderRadius: 12, padding: 14, marginTop: 16, borderWidth: 0,
    backgroundColor: 'rgba(255,255,255,0.02)',
  },
  feedbackTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, marginBottom: 6 },
  feedbackExplanation: { fontFamily: 'PressStart2P_400Regular', fontSize: 7, color: '#CCC', lineHeight: 14 },
  fixedCodeBox: { backgroundColor: 'rgba(0,255,136,0.1)', borderRadius: 8, padding: 10, marginTop: 10 },
  fixedCodeLabel: { fontFamily: 'PressStart2P_400Regular', fontSize: 7, color: '#00FF88', marginBottom: 6 },
  fixedCodeText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#00FF88' },
  footer: { padding: 16 },
  checkButton: { borderRadius: 12, overflow: 'hidden' },
  checkGradient: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 16, gap: 10 },
  checkText: { fontFamily: 'PressStart2P_400Regular', fontSize: 12, color: '#FFF' },
  nextButton: { borderRadius: 12, overflow: 'hidden' },
  nextGradient: { alignItems: 'center', justifyContent: 'center', paddingVertical: 16 },
  nextText: { fontFamily: 'PressStart2P_400Regular', fontSize: 12, color: '#0D0D0D' },
  resultsContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  resultsIcon: {
    width: 120, height: 120, borderRadius: 60,
    backgroundColor: 'rgba(255,107,107,0.1)', justifyContent: 'center', alignItems: 'center', marginBottom: 24,
  },
  resultsTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 16, color: '#FF6B6B', marginBottom: 12, textAlign: 'center' },
  resultsScore: { fontFamily: 'PressStart2P_400Regular', fontSize: 14, color: '#FFF', marginBottom: 24 },
  resultsStats: { flexDirection: 'row', gap: 24, marginBottom: 32 },
  resultsStat: { alignItems: 'center', gap: 6 },
  resultsStatText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#FFF' },
  playAgainButton: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: 'rgba(255,107,107,0.1)', borderWidth: 0, borderColor: '#FF6B6B',
    borderRadius: 12, paddingVertical: 14, paddingHorizontal: 24, marginBottom: 12,
  },
  playAgainText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#FF6B6B' },
  backToGamesButton: { paddingVertical: 12 },
  backToGamesText: { fontFamily: 'PressStart2P_400Regular', fontSize: 9, color: '#888' },
});
