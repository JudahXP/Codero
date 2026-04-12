import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Keyboard,
  BackHandler,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/services/api';
import { useAuth } from '../../src/context/AuthContext';
import * as Haptics from 'expo-haptics';

export default function SpeedCodeScreen() {
  const router = useRouter();
  const { lang } = useLocalSearchParams<{ lang: string }>();
  const { refreshUser } = useAuth();
  const language = lang || 'python';
  const [challenges, setChallenges] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [current, setCurrent] = useState(0);
  const [input, setInput] = useState('');
  const [timeLeft, setTimeLeft] = useState(0);
  const [checked, setChecked] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [totalPoints, setTotalPoints] = useState(0);
  const [correctCount, setCorrectCount] = useState(0);
  const [gameOver, setGameOver] = useState(false);
  const [gameResults, setGameResults] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);
  const [started, setStarted] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const inputRef = useRef<TextInput>(null);

  const handleExit = useCallback(() => {
    if (gameOver || !started) { router.back(); return; }
    if (timerRef.current) clearInterval(timerRef.current);
    Alert.alert('QUIT GAME?', 'Your progress will be lost!', [
      { text: 'KEEP PLAYING', style: 'cancel', onPress: () => {
        if (!checked && timeLeft > 0) {
          timerRef.current = setInterval(() => {
            setTimeLeft(t => { if (t <= 1) { clearInterval(timerRef.current!); return 0; } return t - 1; });
          }, 1000);
        }
      }},
      { text: 'QUIT', style: 'destructive', onPress: () => router.back() },
    ]);
  }, [gameOver, started, router, checked, timeLeft]);

  useEffect(() => {
    const bh = BackHandler.addEventListener('hardwareBackPress', () => { handleExit(); return true; });
    return () => bh.remove();
  }, [handleExit]);

  useEffect(() => { fetchChallenges(); }, [language]);

  useEffect(() => {
    if (started && timeLeft > 0 && !checked) {
      timerRef.current = setInterval(() => {
        setTimeLeft(t => {
          if (t <= 1) {
            clearInterval(timerRef.current!);
            handleTimeUp();
            return 0;
          }
          return t - 1;
        });
      }, 1000);
      return () => { if (timerRef.current) clearInterval(timerRef.current); };
    }
  }, [started, current, checked]);

  const fetchChallenges = async () => {
    try {
      const res = await api.get(`/games/speed-code/${language}`);
      setChallenges(res.data.challenges);
    } catch (e) {
      Alert.alert('ERROR', 'Failed to load challenges');
      router.back();
    } finally {
      setLoading(false);
    }
  };

  const startChallenge = () => {
    setStarted(true);
    setTimeLeft(challenges[current].time_limit);
    setTimeout(() => inputRef.current?.focus(), 300);
  };

  const handleTimeUp = () => {
    if (!checked) {
      setChecked(true);
      setResult({ correct: false, expected: challenges[current]?.prompt || '', points: 0, timed_out: true });
    }
  };

  const handleSubmit = async () => {
    if (timerRef.current) clearInterval(timerRef.current);
    Keyboard.dismiss();
    if (!input.trim()) {
      Alert.alert('TYPE CODE', 'Write your code first!');
      return;
    }
    try {
      const res = await api.post(`/games/speed-code/${language}/check`, {
        challenge_id: challenges[current].id,
        code: input,
      });
      setResult(res.data);
      setChecked(true);
      if (res.data.correct) {
        setTotalPoints(p => p + res.data.points);
        setCorrectCount(c => c + 1);
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
      const nextIdx = current + 1;
      setCurrent(nextIdx);
      setInput('');
      setChecked(false);
      setResult(null);
      setTimeLeft(challenges[nextIdx].time_limit);
      setStarted(true);
      setTimeout(() => inputRef.current?.focus(), 300);
    } else {
      setSubmitting(true);
      try {
        const res = await api.post('/games/complete', {
          game_type: 'speed_code', score: correctCount, total: challenges.length, language,
        });
        setGameResults(res.data);
        setGameOver(true);
        await refreshUser();
      } catch (e) {
        setGameOver(true);
        setGameResults({ xp_earned: 0, score_pct: Math.round((correctCount / challenges.length) * 100) });
      } finally {
        setSubmitting(false);
      }
    }
  };

  if (loading) {
    return (
      <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
        <SafeAreaView style={styles.centered}>
          <ActivityIndicator size="large" color="#FFD700" />
          <Text style={styles.loadingText}>WARMING UP...</Text>
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
              <Ionicons name="flash" size={60} color="#FFD700" />
            </View>
            <Text style={styles.resultsTitle}>
              {correctCount >= 4 ? 'SPEED DEMON!' : correctCount >= 3 ? 'FAST CODER!' : 'GETTING FASTER!'}
            </Text>
            <Text style={styles.resultsScore}>{correctCount}/{challenges.length} CORRECT</Text>
            <Text style={styles.pointsText}>{totalPoints} POINTS</Text>
            {gameResults && (
              <View style={styles.resultsStats}>
                <View style={styles.resultsStat}>
                  <Ionicons name="star" size={20} color="#FFD700" />
                  <Text style={styles.resultsStatText}>+{gameResults.xp_earned} XP</Text>
                </View>
              </View>
            )}
            <TouchableOpacity style={styles.playAgainButton} onPress={() => {
              setCurrent(0); setTotalPoints(0); setCorrectCount(0); setInput(''); setChecked(false);
              setResult(null); setGameOver(false); setGameResults(null); setStarted(false); setLoading(true); fetchChallenges();
            }}>
              <Ionicons name="refresh" size={18} color="#FFD700" />
              <Text style={styles.playAgainText}>PLAY AGAIN</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
              <Text style={styles.backBtnText}>BACK TO GAMES</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  const challenge = challenges[current];
  const timerPct = challenge ? (timeLeft / challenge.time_limit) * 100 : 100;
  const timerColor = timerPct > 50 ? '#00FF88' : timerPct > 25 ? '#FFD700' : '#FF6B6B';

  if (!started) {
    return (
      <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.startContainer}>
            <View style={styles.startIcon}>
              <Ionicons name="flash" size={60} color="#FFD700" />
            </View>
            <Text style={styles.startTitle}>SPEED CODE</Text>
            <Text style={styles.startDesc}>TYPE THE CODE AS FAST AS YOU CAN!</Text>
            <Text style={styles.startTip}>YOU HAVE LIMITED TIME FOR EACH CHALLENGE</Text>
            <View style={styles.startInfo}>
              <Text style={styles.startInfoText}>{challenges.length} CHALLENGES</Text>
              <Text style={styles.startInfoText}>{language.toUpperCase()}</Text>
            </View>
            <TouchableOpacity style={styles.goButton} onPress={startChallenge}>
              <LinearGradient colors={['#FFD700', '#FFA500']} style={styles.goGradient}>
                <Ionicons name="play" size={24} color="#0D0D0D" />
                <Text style={styles.goText}>GO!</Text>
              </LinearGradient>
            </TouchableOpacity>
            <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
              <Text style={styles.backBtnText}>BACK TO GAMES</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  return (
    <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
          <View style={styles.header}>
            <TouchableOpacity style={styles.closeButton} onPress={handleExit}>
              <Ionicons name="close" size={24} color="#FFD700" />
            </TouchableOpacity>
            <View style={styles.timerContainer}>
              <View style={styles.timerBar}>
                <View style={[styles.timerFill, { width: `${timerPct}%`, backgroundColor: timerColor }]} />
              </View>
              <Text style={[styles.timerText, { color: timerColor }]}>{timeLeft}s</Text>
            </View>
            <Text style={styles.counterText}>{current + 1}/{challenges.length}</Text>
          </View>

          <View style={styles.mainContent}>
            <View style={styles.conceptBadge}>
              <Ionicons name="school" size={14} color="#FFD700" />
              <Text style={styles.conceptText}>{challenge.concept.toUpperCase()}</Text>
            </View>

            <Text style={styles.prompt}>{challenge.prompt}</Text>
            <Text style={styles.pointsLabel}>+{challenge.points} POINTS</Text>

            <TextInput
              ref={inputRef}
              style={styles.codeInput}
              value={input}
              onChangeText={setInput}
              placeholder="TYPE YOUR CODE..."
              placeholderTextColor="#555"
              autoCapitalize="none"
              autoCorrect={false}
              editable={!checked}
              onSubmitEditing={handleSubmit}
            />

            {checked && result && (
              <View style={[styles.feedbackBox, { borderColor: result.correct ? '#00FF88' : '#FF6B6B' }]}>
                <Ionicons name={result.correct ? 'checkmark-circle' : result.timed_out ? 'timer' : 'close-circle'} size={20} color={result.correct ? '#00FF88' : '#FF6B6B'} />
                <View style={{ flex: 1 }}>
                  <Text style={[styles.feedbackTitle, { color: result.correct ? '#00FF88' : '#FF6B6B' }]}>
                    {result.correct ? 'PERFECT!' : result.timed_out ? 'TIME\'S UP!' : 'CLOSE!'}
                  </Text>
                  {!result.correct && result.expected && (
                    <View style={styles.expectedBox}>
                      <Text style={styles.expectedLabel}>EXPECTED:</Text>
                      <Text style={styles.expectedCode}>{result.expected}</Text>
                    </View>
                  )}
                </View>
              </View>
            )}
          </View>

          <View style={styles.footer}>
            {!checked ? (
              <TouchableOpacity style={styles.submitBtn} onPress={handleSubmit}>
                <LinearGradient colors={['#FFD700', '#FFA500']} style={styles.submitGrad}>
                  <Ionicons name="send" size={18} color="#0D0D0D" />
                  <Text style={styles.submitText}>SUBMIT</Text>
                </LinearGradient>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity style={styles.nextBtn} onPress={handleNext} disabled={submitting}>
                <LinearGradient colors={['#00FF88', '#00CC6A']} style={styles.nextGrad}>
                  {submitting ? <ActivityIndicator color="#0D0D0D" /> : (
                    <Text style={styles.nextBtnText}>{current < challenges.length - 1 ? 'NEXT' : 'RESULTS'}</Text>
                  )}
                </LinearGradient>
              </TouchableOpacity>
            )}
          </View>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#FFD700', marginTop: 16 },
  header: { flexDirection: 'row', alignItems: 'center', padding: 16, gap: 12 },
  closeButton: {
    width: 40, height: 40, borderRadius: 10,
    backgroundColor: 'rgba(255,215,0,0.1)', justifyContent: 'center', alignItems: 'center',
  },
  timerContainer: { flex: 1, gap: 4 },
  timerBar: { height: 8, backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 4, overflow: 'hidden' },
  timerFill: { height: '100%', borderRadius: 4 },
  timerText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, textAlign: 'center' },
  counterText: { fontFamily: 'PressStart2P_400Regular', fontSize: 9, color: '#FFD700' },
  mainContent: { flex: 1, padding: 16 },
  conceptBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: 'rgba(255,215,0,0.1)', borderRadius: 8,
    paddingHorizontal: 10, paddingVertical: 6, alignSelf: 'flex-start', marginBottom: 20,
  },
  conceptText: { fontFamily: 'PressStart2P_400Regular', fontSize: 6, color: '#FFD700' },
  prompt: { fontFamily: 'PressStart2P_400Regular', fontSize: 14, color: '#FFF', lineHeight: 24, marginBottom: 8 },
  pointsLabel: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#FFD700', marginBottom: 20 },
  codeInput: {
    backgroundColor: '#1a1a1a', borderRadius: 12, padding: 16, minHeight: 56,
    fontFamily: 'PressStart2P_400Regular', fontSize: 11, color: '#00FF88',
    borderWidth: 2, borderColor: 'rgba(255,215,0,0.3)',
  },
  feedbackBox: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 12,
    borderRadius: 12, padding: 14, marginTop: 16, borderWidth: 1,
    backgroundColor: 'rgba(255,255,255,0.02)',
  },
  feedbackTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, marginBottom: 6 },
  expectedBox: { backgroundColor: 'rgba(0,255,136,0.1)', borderRadius: 8, padding: 10, marginTop: 8 },
  expectedLabel: { fontFamily: 'PressStart2P_400Regular', fontSize: 7, color: '#00FF88', marginBottom: 6 },
  expectedCode: { fontFamily: 'PressStart2P_400Regular', fontSize: 9, color: '#00FF88' },
  footer: { padding: 16 },
  submitBtn: { borderRadius: 12, overflow: 'hidden' },
  submitGrad: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 16, gap: 10 },
  submitText: { fontFamily: 'PressStart2P_400Regular', fontSize: 12, color: '#0D0D0D' },
  nextBtn: { borderRadius: 12, overflow: 'hidden' },
  nextGrad: { alignItems: 'center', justifyContent: 'center', paddingVertical: 16 },
  nextBtnText: { fontFamily: 'PressStart2P_400Regular', fontSize: 12, color: '#0D0D0D' },
  startContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  startIcon: {
    width: 120, height: 120, borderRadius: 60,
    backgroundColor: 'rgba(255,215,0,0.1)', justifyContent: 'center', alignItems: 'center', marginBottom: 24,
  },
  startTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 20, color: '#FFD700', marginBottom: 16 },
  startDesc: { fontFamily: 'PressStart2P_400Regular', fontSize: 9, color: '#FFF', textAlign: 'center', marginBottom: 8 },
  startTip: { fontFamily: 'PressStart2P_400Regular', fontSize: 7, color: '#888', textAlign: 'center', marginBottom: 24 },
  startInfo: { flexDirection: 'row', gap: 24, marginBottom: 32 },
  startInfoText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#FFD700' },
  goButton: { borderRadius: 16, overflow: 'hidden', width: '80%', marginBottom: 16 },
  goGradient: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 18, gap: 12 },
  goText: { fontFamily: 'PressStart2P_400Regular', fontSize: 20, color: '#0D0D0D' },
  resultsContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  resultsIcon: {
    width: 120, height: 120, borderRadius: 60,
    backgroundColor: 'rgba(255,215,0,0.1)', justifyContent: 'center', alignItems: 'center', marginBottom: 24,
  },
  resultsTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 16, color: '#FFD700', marginBottom: 12, textAlign: 'center' },
  resultsScore: { fontFamily: 'PressStart2P_400Regular', fontSize: 14, color: '#FFF', marginBottom: 8 },
  pointsText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#FFD700', marginBottom: 24 },
  resultsStats: { flexDirection: 'row', gap: 24, marginBottom: 32 },
  resultsStat: { alignItems: 'center', gap: 6 },
  resultsStatText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#FFF' },
  playAgainButton: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: 'rgba(255,215,0,0.1)', borderWidth: 1, borderColor: '#FFD700',
    borderRadius: 12, paddingVertical: 14, paddingHorizontal: 24, marginBottom: 12,
  },
  playAgainText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#FFD700' },
  backBtn: { paddingVertical: 12 },
  backBtnText: { fontFamily: 'PressStart2P_400Regular', fontSize: 9, color: '#888' },
});
