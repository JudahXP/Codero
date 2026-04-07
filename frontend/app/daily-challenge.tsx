import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../src/services/api';
import { useAuth } from '../src/context/AuthContext';

interface Exercise {
  type: 'multiple_choice' | 'code' | 'fill_blank';
  question: string;
  options?: string[];
  correct?: number;
  solution?: string;
  hint?: string;
  answer?: string;
}

interface Challenge {
  id: string;
  type: string;
  title: string;
  description: string;
  xp_reward: number;
  gem_reward: number;
  time_limit: number;
  exercises: Exercise[];
  completed: boolean;
}

export default function DailyChallengeScreen() {
  const router = useRouter();
  const { refreshUser } = useAuth();
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [loading, setLoading] = useState(true);
  const [started, setStarted] = useState(false);
  const [currentExercise, setCurrentExercise] = useState(0);
  const [answers, setAnswers] = useState<any[]>([]);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [codeInput, setCodeInput] = useState('');
  const [fillInput, setFillInput] = useState('');
  const [timeLeft, setTimeLeft] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [results, setResults] = useState<any>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    fetchChallenge();
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  useEffect(() => {
    if (started && timeLeft > 0) {
      timerRef.current = setInterval(() => {
        setTimeLeft((t) => {
          if (t <= 1) {
            if (timerRef.current) clearInterval(timerRef.current);
            submitChallenge(answers);
            return 0;
          }
          return t - 1;
        });
      }, 1000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [started]);

  const fetchChallenge = async () => {
    try {
      const response = await api.get('/daily-challenge');
      setChallenge(response.data);
      setTimeLeft(response.data.time_limit);
      setAnswers(new Array(response.data.exercises.length).fill(null));
    } catch (error) {
      console.error('Failed to fetch challenge:', error);
    } finally {
      setLoading(false);
    }
  };

  const startChallenge = () => {
    if (challenge?.completed) {
      Alert.alert('COMPLETED', 'You already completed today\'s challenge!');
      return;
    }
    setStarted(true);
  };

  const handleNext = () => {
    if (!challenge) return;

    const exercise = challenge.exercises[currentExercise];
    let answer: any = null;

    if (exercise.type === 'multiple_choice') {
      if (selectedOption === null) {
        Alert.alert('SELECT', 'Pick an answer!');
        return;
      }
      answer = { selected: selectedOption };
    } else if (exercise.type === 'code') {
      if (!codeInput.trim()) {
        Alert.alert('CODE', 'Write some code!');
        return;
      }
      answer = { code: codeInput };
    } else if (exercise.type === 'fill_blank') {
      if (!fillInput.trim()) {
        Alert.alert('FILL', 'Fill in the blank!');
        return;
      }
      answer = { answer: fillInput };
    }

    const newAnswers = [...answers];
    newAnswers[currentExercise] = answer;
    setAnswers(newAnswers);

    if (currentExercise < challenge.exercises.length - 1) {
      setCurrentExercise(currentExercise + 1);
      setSelectedOption(null);
      setCodeInput('');
      setFillInput('');
    } else {
      submitChallenge(newAnswers);
    }
  };

  const submitChallenge = async (finalAnswers: any[]) => {
    if (timerRef.current) clearInterval(timerRef.current);
    setSubmitting(true);
    try {
      const response = await api.post('/daily-challenge/complete', {
        challenge_id: challenge?.id,
        answers: finalAnswers,
      });
      setResults(response.data);
      await refreshUser();
    } catch (error: any) {
      Alert.alert('ERROR', error.response?.data?.detail || 'Failed to submit');
    } finally {
      setSubmitting(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
        <SafeAreaView style={styles.centered}>
          <ActivityIndicator size="large" color="#00FF88" />
          <Text style={styles.loadingText}>LOADING...</Text>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  if (results) {
    return (
      <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.resultsContainer}>
            <View style={styles.resultsIcon}>
              <Ionicons
                name={results.passed ? 'trophy' : 'refresh'}
                size={60}
                color={results.passed ? '#FFD700' : '#FF6B6B'}
              />
            </View>
            <Text style={styles.resultsTitle}>
              {results.passed ? 'CHALLENGE COMPLETE!' : 'TRY AGAIN TOMORROW'}
            </Text>
            <Text style={styles.resultsScore}>{results.score}%</Text>
            <Text style={styles.resultsDetail}>
              {results.correct}/{results.total} CORRECT
            </Text>

            {results.passed && (
              <View style={styles.rewardsRow}>
                <View style={styles.rewardBox}>
                  <Ionicons name="star" size={28} color="#FFD700" />
                  <Text style={styles.rewardValue}>+{results.xp_earned}</Text>
                  <Text style={styles.rewardLabel}>XP</Text>
                </View>
                <View style={styles.rewardBox}>
                  <Ionicons name="diamond" size={28} color="#00BFFF" />
                  <Text style={styles.rewardValue}>+{results.gems_earned}</Text>
                  <Text style={styles.rewardLabel}>GEMS</Text>
                </View>
              </View>
            )}

            <TouchableOpacity style={styles.continueButton} onPress={() => router.back()}>
              <LinearGradient colors={['#00FF88', '#00CC6A']} style={styles.continueGradient}>
                <Text style={styles.continueText}>CONTINUE</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  if (!started) {
    return (
      <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
              <Ionicons name="arrow-back" size={24} color="#00FF88" />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>DAILY CHALLENGE</Text>
            <View style={{ width: 44 }} />
          </View>

          <View style={styles.challengeIntro}>
            <View style={styles.challengeIconBox}>
              <Ionicons name="flash" size={48} color="#FFD700" />
            </View>
            <Text style={styles.challengeTitle}>{challenge?.title?.toUpperCase()}</Text>
            <Text style={styles.challengeDesc}>{challenge?.description?.toUpperCase()}</Text>

            <View style={styles.rewardsPreview}>
              <View style={styles.rewardPreviewItem}>
                <Ionicons name="star" size={24} color="#FFD700" />
                <Text style={styles.rewardPreviewText}>{challenge?.xp_reward} XP</Text>
              </View>
              <View style={styles.rewardPreviewItem}>
                <Ionicons name="diamond" size={24} color="#00BFFF" />
                <Text style={styles.rewardPreviewText}>{challenge?.gem_reward} GEMS</Text>
              </View>
              <View style={styles.rewardPreviewItem}>
                <Ionicons name="time" size={24} color="#FF6B6B" />
                <Text style={styles.rewardPreviewText}>{formatTime(challenge?.time_limit || 0)}</Text>
              </View>
            </View>

            {challenge?.completed ? (
              <View style={styles.completedBadge}>
                <Ionicons name="checkmark-circle" size={24} color="#00FF88" />
                <Text style={styles.completedText}>COMPLETED TODAY</Text>
              </View>
            ) : (
              <TouchableOpacity style={styles.startButton} onPress={startChallenge}>
                <LinearGradient colors={['#FFD700', '#FFA500']} style={styles.startGradient}>
                  <Ionicons name="play" size={24} color="#0D0D0D" />
                  <Text style={styles.startText}>START</Text>
                </LinearGradient>
              </TouchableOpacity>
            )}
          </View>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  const exercise = challenge?.exercises[currentExercise];
  if (!exercise) return null;

  return (
    <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        {/* Timer Header */}
        <View style={styles.timerHeader}>
          <View style={styles.progressBar}>
            <View
              style={[
                styles.progressFill,
                { width: `${((currentExercise + 1) / (challenge?.exercises.length || 1)) * 100}%` },
              ]}
            />
          </View>
          <View style={[
            styles.timerBox,
            timeLeft < 30 && styles.timerBoxUrgent,
          ]}>
            <Ionicons name="time" size={18} color={timeLeft < 30 ? '#FF6B6B' : '#FFD700'} />
            <Text style={[styles.timerText, timeLeft < 30 && styles.timerTextUrgent]}>
              {formatTime(timeLeft)}
            </Text>
          </View>
        </View>

        <ScrollView style={styles.content} contentContainerStyle={styles.contentInner}>
          <Text style={styles.question}>{exercise.question}</Text>

          {exercise.type === 'multiple_choice' && exercise.options && (
            <View style={styles.optionsContainer}>
              {exercise.options.map((option, index) => (
                <TouchableOpacity
                  key={index}
                  style={[styles.optionButton, selectedOption === index && styles.optionSelected]}
                  onPress={() => setSelectedOption(index)}
                >
                  <Text style={[styles.optionText, selectedOption === index && styles.optionTextSelected]}>
                    {option}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          )}

          {exercise.type === 'code' && (
            <TextInput
              style={styles.codeInput}
              value={codeInput}
              onChangeText={setCodeInput}
              multiline
              placeholder="WRITE YOUR CODE..."
              placeholderTextColor="#555"
              autoCapitalize="none"
            />
          )}

          {exercise.type === 'fill_blank' && (
            <TextInput
              style={styles.fillInput}
              value={fillInput}
              onChangeText={setFillInput}
              placeholder="YOUR ANSWER..."
              placeholderTextColor="#555"
              autoCapitalize="none"
            />
          )}
        </ScrollView>

        <View style={styles.footer}>
          <TouchableOpacity style={styles.submitButton} onPress={handleNext} disabled={submitting}>
            <LinearGradient colors={['#00FF88', '#00CC6A']} style={styles.submitGradient}>
              {submitting ? (
                <ActivityIndicator color="#0D0D0D" />
              ) : (
                <Text style={styles.submitText}>
                  {currentExercise < (challenge?.exercises.length || 1) - 1 ? 'NEXT' : 'FINISH'}
                </Text>
              )}
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#00FF88', marginTop: 16 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 20 },
  backButton: {
    width: 44, height: 44, borderRadius: 12,
    backgroundColor: 'rgba(0, 255, 136, 0.1)', borderWidth: 1, borderColor: '#00FF88',
    justifyContent: 'center', alignItems: 'center',
  },
  headerTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 12, color: '#FFD700' },
  challengeIntro: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  challengeIconBox: {
    width: 100, height: 100, borderRadius: 50,
    backgroundColor: 'rgba(255, 215, 0, 0.1)', borderWidth: 2, borderColor: '#FFD700',
    justifyContent: 'center', alignItems: 'center', marginBottom: 24,
  },
  challengeTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 16, color: '#FFD700', marginBottom: 12 },
  challengeDesc: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#888', textAlign: 'center', marginBottom: 32 },
  rewardsPreview: { flexDirection: 'row', gap: 20, marginBottom: 40 },
  rewardPreviewItem: { alignItems: 'center', gap: 8 },
  rewardPreviewText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#FFF' },
  startButton: { borderRadius: 12, overflow: 'hidden', width: '100%' },
  startGradient: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 16, gap: 12 },
  startText: { fontFamily: 'PressStart2P_400Regular', fontSize: 14, color: '#0D0D0D' },
  completedBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: 'rgba(0, 255, 136, 0.1)', borderRadius: 12,
    paddingHorizontal: 20, paddingVertical: 16, borderWidth: 1, borderColor: '#00FF88',
  },
  completedText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#00FF88' },
  timerHeader: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingVertical: 12, gap: 12 },
  progressBar: { flex: 1, height: 8, backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 4, overflow: 'hidden' },
  progressFill: { height: '100%', backgroundColor: '#FFD700', borderRadius: 4 },
  timerBox: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: 'rgba(255, 215, 0, 0.1)', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8,
  },
  timerBoxUrgent: { backgroundColor: 'rgba(255, 107, 107, 0.2)' },
  timerText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#FFD700' },
  timerTextUrgent: { color: '#FF6B6B' },
  content: { flex: 1 },
  contentInner: { padding: 20 },
  question: { fontFamily: 'PressStart2P_400Regular', fontSize: 11, color: '#FFF', lineHeight: 22, marginBottom: 24 },
  optionsContainer: { gap: 12 },
  optionButton: {
    backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 12, padding: 16,
    borderWidth: 2, borderColor: 'rgba(255,255,255,0.1)',
  },
  optionSelected: { borderColor: '#FFD700', backgroundColor: 'rgba(255, 215, 0, 0.1)' },
  optionText: { fontFamily: 'PressStart2P_400Regular', fontSize: 9, color: '#AAA' },
  optionTextSelected: { color: '#FFD700' },
  codeInput: {
    backgroundColor: '#1a1a1a', borderRadius: 12, padding: 16, minHeight: 120,
    fontFamily: 'PressStart2P_400Regular', fontSize: 9, color: '#00FF88', borderWidth: 1, borderColor: '#333',
  },
  fillInput: {
    backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 12, padding: 16,
    fontFamily: 'PressStart2P_400Regular', fontSize: 12, color: '#FFF', textAlign: 'center',
    borderWidth: 2, borderColor: 'rgba(255, 215, 0, 0.3)',
  },
  footer: { padding: 20 },
  submitButton: { borderRadius: 12, overflow: 'hidden' },
  submitGradient: { alignItems: 'center', justifyContent: 'center', paddingVertical: 16 },
  submitText: { fontFamily: 'PressStart2P_400Regular', fontSize: 12, color: '#0D0D0D' },
  resultsContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  resultsIcon: {
    width: 120, height: 120, borderRadius: 60,
    backgroundColor: 'rgba(255, 215, 0, 0.1)', justifyContent: 'center', alignItems: 'center', marginBottom: 24,
  },
  resultsTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 14, color: '#FFD700', marginBottom: 16, textAlign: 'center' },
  resultsScore: { fontFamily: 'PressStart2P_400Regular', fontSize: 32, color: '#FFF', marginBottom: 8 },
  resultsDetail: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#888', marginBottom: 32 },
  rewardsRow: { flexDirection: 'row', gap: 32, marginBottom: 40 },
  rewardBox: { alignItems: 'center', gap: 8 },
  rewardValue: { fontFamily: 'PressStart2P_400Regular', fontSize: 14, color: '#FFF' },
  rewardLabel: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#888' },
  continueButton: { borderRadius: 12, overflow: 'hidden', width: '100%' },
  continueGradient: { alignItems: 'center', justifyContent: 'center', paddingVertical: 16 },
  continueText: { fontFamily: 'PressStart2P_400Regular', fontSize: 14, color: '#0D0D0D' },
});
