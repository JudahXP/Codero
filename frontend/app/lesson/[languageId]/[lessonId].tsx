import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../../src/services/api';
import { useAuth } from '../../../src/context/AuthContext';

interface Exercise {
  type: 'multiple_choice' | 'code' | 'fill_blank';
  question: string;
  options?: string[];
  correct?: number;
  starter?: string;
  solution?: string;
  hint?: string;
  answer?: string;
}

interface Lesson {
  id: string;
  title: string;
  description: string;
  xp: number;
  unit: number;
  exercises: Exercise[];
}

export default function LessonScreen() {
  const router = useRouter();
  const { languageId, lessonId } = useLocalSearchParams<{ languageId: string; lessonId: string }>();
  const { refreshUser } = useAuth();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentExercise, setCurrentExercise] = useState(0);
  const [answers, setAnswers] = useState<any[]>([]);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [codeInput, setCodeInput] = useState('');
  const [fillInput, setFillInput] = useState('');
  const [showHint, setShowHint] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [results, setResults] = useState<any>(null);

  useEffect(() => {
    fetchLesson();
  }, [languageId, lessonId]);

  const fetchLesson = async () => {
    try {
      const response = await api.get(`/languages/${languageId}/lessons/${lessonId}`);
      setLesson(response.data);
      setAnswers(new Array(response.data.exercises.length).fill(null));
      if (response.data.exercises[0]?.starter) {
        setCodeInput(response.data.exercises[0].starter);
      }
    } catch (error) {
      console.error('Failed to fetch lesson:', error);
      Alert.alert('ERROR', 'Failed to load lesson');
      router.back();
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    if (!lesson) return;

    const exercise = lesson.exercises[currentExercise];
    let answer: any = null;

    if (exercise.type === 'multiple_choice') {
      if (selectedOption === null) {
        Alert.alert('SELECT ANSWER', 'Please select an option');
        return;
      }
      answer = { selected: selectedOption };
    } else if (exercise.type === 'code') {
      if (!codeInput.trim()) {
        Alert.alert('WRITE CODE', 'Please write some code');
        return;
      }
      answer = { code: codeInput };
    } else if (exercise.type === 'fill_blank') {
      if (!fillInput.trim()) {
        Alert.alert('FILL BLANK', 'Please fill in the blank');
        return;
      }
      answer = { answer: fillInput };
    }

    const newAnswers = [...answers];
    newAnswers[currentExercise] = answer;
    setAnswers(newAnswers);

    if (currentExercise < lesson.exercises.length - 1) {
      const nextExercise = currentExercise + 1;
      setCurrentExercise(nextExercise);
      setSelectedOption(null);
      setFillInput('');
      setShowHint(false);
      if (lesson.exercises[nextExercise]?.starter) {
        setCodeInput(lesson.exercises[nextExercise].starter);
      } else {
        setCodeInput('');
      }
    } else {
      // Submit lesson
      submitLesson(newAnswers);
    }
  };

  const submitLesson = async (finalAnswers: any[]) => {
    setSubmitting(true);
    try {
      const response = await api.post('/progress/complete', {
        lesson_id: lessonId,
        language: languageId,
        answers: finalAnswers,
      });
      setResults(response.data);
      setCompleted(true);
      await refreshUser();
    } catch (error: any) {
      Alert.alert('ERROR', error.response?.data?.detail || 'Failed to submit');
    } finally {
      setSubmitting(false);
    }
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

  if (completed && results) {
    return (
      <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.resultsContainer}>
            <View style={styles.resultsIcon}>
              <Ionicons
                name={results.score >= 70 ? 'trophy' : 'refresh'}
                size={60}
                color={results.score >= 70 ? '#FFD700' : '#FF6B6B'}
              />
            </View>
            <Text style={styles.resultsTitle}>
              {results.score >= 70 ? 'GREAT JOB!' : 'KEEP TRYING!'}
            </Text>
            <Text style={styles.resultsScore}>{results.score}% CORRECT</Text>
            <Text style={styles.resultsDetail}>
              {results.correct}/{results.total} ANSWERS
            </Text>

            <View style={styles.resultsStats}>
              <View style={styles.resultsStat}>
                <Ionicons name="star" size={24} color="#FFD700" />
                <Text style={styles.resultsStatValue}>+{results.xp_earned} XP</Text>
              </View>
              {results.new_badges?.length > 0 && (
                <View style={styles.resultsStat}>
                  <Ionicons name="medal" size={24} color="#FF6B6B" />
                  <Text style={styles.resultsStatValue}>NEW BADGE!</Text>
                </View>
              )}
            </View>

            <TouchableOpacity
              style={styles.continueButton}
              onPress={() => router.back()}
            >
              <LinearGradient
                colors={['#00FF88', '#00CC6A']}
                style={styles.continueGradient}
              >
                <Text style={styles.continueText}>CONTINUE</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  const exercise = lesson?.exercises[currentExercise];
  if (!exercise) return null;

  return (
    <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardView}
        >
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity style={styles.closeButton} onPress={() => router.back()}>
              <Ionicons name="close" size={24} color="#FF6B6B" />
            </TouchableOpacity>
            <View style={styles.progressBar}>
              <View
                style={[
                  styles.progressFill,
                  { width: `${((currentExercise + 1) / (lesson?.exercises.length || 1)) * 100}%` },
                ]}
              />
            </View>
            <Text style={styles.progressText}>
              {currentExercise + 1}/{lesson?.exercises.length}
            </Text>
          </View>

          <ScrollView style={styles.content} contentContainerStyle={styles.contentInner}>
            {/* Exercise Type Badge */}
            <View style={styles.typeBadge}>
              <Ionicons
                name={
                  exercise.type === 'multiple_choice'
                    ? 'list'
                    : exercise.type === 'code'
                    ? 'code-slash'
                    : 'create'
                }
                size={16}
                color="#00FF88"
              />
              <Text style={styles.typeText}>
                {exercise.type === 'multiple_choice'
                  ? 'MULTIPLE CHOICE'
                  : exercise.type === 'code'
                  ? 'CODE CHALLENGE'
                  : 'FILL THE BLANK'}
              </Text>
            </View>

            {/* Question */}
            <Text style={styles.question}>{exercise.question}</Text>

            {/* Multiple Choice */}
            {exercise.type === 'multiple_choice' && exercise.options && (
              <View style={styles.optionsContainer}>
                {exercise.options.map((option, index) => (
                  <TouchableOpacity
                    key={index}
                    style={[
                      styles.optionButton,
                      selectedOption === index && styles.optionSelected,
                    ]}
                    onPress={() => setSelectedOption(index)}
                  >
                    <View style={[
                      styles.optionCircle,
                      selectedOption === index && styles.optionCircleSelected,
                    ]}>
                      {selectedOption === index && (
                        <Ionicons name="checkmark" size={14} color="#0D0D0D" />
                      )}
                    </View>
                    <Text style={[
                      styles.optionText,
                      selectedOption === index && styles.optionTextSelected,
                    ]}>
                      {option}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}

            {/* Code Input */}
            {exercise.type === 'code' && (
              <View style={styles.codeContainer}>
                <TextInput
                  style={styles.codeInput}
                  value={codeInput}
                  onChangeText={setCodeInput}
                  multiline
                  placeholder="WRITE YOUR CODE HERE..."
                  placeholderTextColor="#555"
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              </View>
            )}

            {/* Fill Blank */}
            {exercise.type === 'fill_blank' && (
              <View style={styles.fillContainer}>
                <TextInput
                  style={styles.fillInput}
                  value={fillInput}
                  onChangeText={setFillInput}
                  placeholder="TYPE YOUR ANSWER..."
                  placeholderTextColor="#555"
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              </View>
            )}

            {/* Hint */}
            {exercise.hint && (
              <TouchableOpacity
                style={styles.hintButton}
                onPress={() => setShowHint(!showHint)}
              >
                <Ionicons name="bulb" size={18} color="#FFD700" />
                <Text style={styles.hintButtonText}>
                  {showHint ? 'HIDE HINT' : 'SHOW HINT'}
                </Text>
              </TouchableOpacity>
            )}
            {showHint && exercise.hint && (
              <View style={styles.hintBox}>
                <Text style={styles.hintText}>{exercise.hint}</Text>
              </View>
            )}
          </ScrollView>

          {/* Submit Button */}
          <View style={styles.footer}>
            <TouchableOpacity
              style={styles.submitButton}
              onPress={handleNext}
              disabled={submitting}
            >
              <LinearGradient
                colors={['#00FF88', '#00CC6A']}
                style={styles.submitGradient}
              >
                {submitting ? (
                  <ActivityIndicator color="#0D0D0D" />
                ) : (
                  <>
                    <Text style={styles.submitText}>
                      {currentExercise < (lesson?.exercises.length || 1) - 1 ? 'NEXT' : 'FINISH'}
                    </Text>
                    <Ionicons name="arrow-forward" size={20} color="#0D0D0D" />
                  </>
                )}
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </KeyboardAvoidingView>
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
  keyboardView: {
    flex: 1,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#00FF88',
    marginTop: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    gap: 12,
  },
  closeButton: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: 'rgba(255, 107, 107, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  progressBar: {
    flex: 1,
    height: 8,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#00FF88',
    borderRadius: 4,
  },
  progressText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#888',
  },
  content: {
    flex: 1,
  },
  contentInner: {
    padding: 20,
  },
  typeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(0, 255, 136, 0.1)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    alignSelf: 'flex-start',
    marginBottom: 20,
  },
  typeText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 7,
    color: '#00FF88',
  },
  question: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 11,
    color: '#FFF',
    lineHeight: 22,
    marginBottom: 24,
  },
  optionsContainer: {
    gap: 12,
  },
  optionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  optionSelected: {
    borderColor: '#00FF88',
    backgroundColor: 'rgba(0, 255, 136, 0.1)',
  },
  optionCircle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#555',
    marginRight: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  optionCircleSelected: {
    backgroundColor: '#00FF88',
    borderColor: '#00FF88',
  },
  optionText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#AAA',
    flex: 1,
  },
  optionTextSelected: {
    color: '#FFF',
  },
  codeContainer: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#333',
    minHeight: 150,
  },
  codeInput: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 9,
    color: '#00FF88',
    padding: 16,
    minHeight: 150,
  },
  fillContainer: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: 'rgba(0, 255, 136, 0.3)',
  },
  fillInput: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 12,
    color: '#FFF',
    padding: 16,
    textAlign: 'center',
  },
  hintButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 20,
    alignSelf: 'center',
  },
  hintButtonText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#FFD700',
  },
  hintBox: {
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    borderRadius: 12,
    padding: 16,
    marginTop: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.3)',
  },
  hintText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#FFD700',
    lineHeight: 16,
  },
  footer: {
    padding: 20,
  },
  submitButton: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  submitGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    gap: 12,
  },
  submitText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 12,
    color: '#0D0D0D',
  },
  resultsContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  resultsIcon: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  resultsTitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 20,
    color: '#00FF88',
    marginBottom: 8,
  },
  resultsScore: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 14,
    color: '#FFF',
    marginBottom: 8,
  },
  resultsDetail: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#888',
    marginBottom: 32,
  },
  resultsStats: {
    flexDirection: 'row',
    gap: 32,
    marginBottom: 40,
  },
  resultsStat: {
    alignItems: 'center',
    gap: 8,
  },
  resultsStatValue: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#FFF',
  },
  continueButton: {
    borderRadius: 12,
    overflow: 'hidden',
    width: '100%',
  },
  continueGradient: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
  },
  continueText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 14,
    color: '#0D0D0D',
  },
});
