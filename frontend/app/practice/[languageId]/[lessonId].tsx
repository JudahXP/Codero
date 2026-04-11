import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../../src/services/api';

interface PracticeContent {
  explanation: string;
  syntax: string;
  examples: Array<{ code: string; output: string }>;
  tips: string[];
  common_mistakes: string[];
}

interface Exercise {
  type: string;
  question: string;
  options?: string[];
  correct?: number;
  solution?: string;
  hint?: string;
  answer?: string;
  explanation?: string;
}

interface PracticeData {
  lesson_id: string;
  title: string;
  practice_content: PracticeContent;
  exercises: Exercise[];
}

export default function PracticeModeScreen() {
  const router = useRouter();
  const { languageId, lessonId } = useLocalSearchParams<{ languageId: string; lessonId: string }>();
  const [data, setData] = useState<PracticeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<'learn' | 'practice'>('learn');
  const [currentExercise, setCurrentExercise] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [codeInput, setCodeInput] = useState('');
  const [fillInput, setFillInput] = useState('');
  const [showAnswer, setShowAnswer] = useState(false);
  const [answers, setAnswers] = useState<any[]>([]);
  const [practiceComplete, setPracticeComplete] = useState(false);
  const [practiceResults, setPracticeResults] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchPracticeContent();
  }, [languageId, lessonId]);

  const fetchPracticeContent = async () => {
    try {
      const response = await api.get(`/languages/${languageId}/lessons/${lessonId}/practice`);
      setData(response.data);
      setAnswers(new Array(response.data.exercises.length).fill(null));
    } catch (error) {
      console.error('Failed to fetch practice content:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNext = async () => {
    if (!data) return;

    const exercise = data.exercises[currentExercise];
    let answer: any = null;

    if (exercise.type === 'multiple_choice') {
      answer = { selected: selectedOption };
    } else if (exercise.type === 'code') {
      answer = { code: codeInput };
    } else if (exercise.type === 'fill_blank') {
      answer = { answer: fillInput };
    }

    const newAnswers = [...answers];
    newAnswers[currentExercise] = answer;
    setAnswers(newAnswers);

    if (currentExercise < data.exercises.length - 1) {
      setCurrentExercise(currentExercise + 1);
      setSelectedOption(null);
      setCodeInput('');
      setFillInput('');
      setShowAnswer(false);
    } else {
      // Submit practice
      setSubmitting(true);
      try {
        const response = await api.post('/progress/complete', {
          lesson_id: lessonId,
          language: languageId,
          answers: newAnswers,
          practice_mode: true,
        });
        setPracticeResults(response.data);
        setPracticeComplete(true);
      } catch (error) {
        console.error('Practice submit error:', error);
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
          <Text style={styles.loadingText}>LOADING PRACTICE...</Text>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  if (practiceComplete && practiceResults) {
    return (
      <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.resultsContainer}>
            <View style={styles.resultsIcon}>
              <Ionicons name="school" size={60} color="#00BFFF" />
            </View>
            <Text style={styles.resultsTitle}>PRACTICE COMPLETE!</Text>
            <Text style={styles.resultsScore}>{practiceResults.score}%</Text>
            <Text style={styles.resultsDetail}>
              {practiceResults.correct}/{practiceResults.total} CORRECT
            </Text>

            <View style={styles.practiceNote}>
              <Ionicons name="information-circle" size={20} color="#00BFFF" />
              <Text style={styles.practiceNoteText}>
                NO HEARTS LOST • NO XP GAINED
              </Text>
            </View>

            <Text style={styles.practiceMessage}>
              KEEP PRACTICING UNTIL YOU'RE READY FOR THE REAL LESSON!
            </Text>

            <View style={styles.resultsButtons}>
              <TouchableOpacity
                style={styles.retryButton}
                onPress={() => {
                  setPracticeComplete(false);
                  setCurrentExercise(0);
                  setAnswers(new Array(data?.exercises.length || 0).fill(null));
                  setSelectedOption(null);
                  setCodeInput('');
                  setFillInput('');
                  setShowAnswer(false);
                }}
              >
                <Ionicons name="refresh" size={20} color="#00BFFF" />
                <Text style={styles.retryText}>PRACTICE AGAIN</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.lessonButton}
                onPress={() => router.replace(`/lesson/${languageId}/${lessonId}`)}
              >
                <LinearGradient colors={['#00FF88', '#00CC6A']} style={styles.lessonGradient}>
                  <Ionicons name="play" size={20} color="#0D0D0D" />
                  <Text style={styles.lessonText}>START LESSON</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>
          </View>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  const content = data?.practice_content;
  const exercise = data?.exercises[currentExercise];

  return (
    <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={{ flex: 1 }}
        >
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity style={styles.closeButton} onPress={() => router.back()}>
              <Ionicons name="close" size={24} color="#00BFFF" />
            </TouchableOpacity>
            <View style={styles.modeTabs}>
              <TouchableOpacity
                style={[styles.modeTab, mode === 'learn' && styles.modeTabActive]}
                onPress={() => setMode('learn')}
              >
                <Text style={[styles.modeTabText, mode === 'learn' && styles.modeTabTextActive]}>
                  LEARN
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modeTab, mode === 'practice' && styles.modeTabActive]}
                onPress={() => setMode('practice')}
              >
                <Text style={[styles.modeTabText, mode === 'practice' && styles.modeTabTextActive]}>
                  PRACTICE
                </Text>
              </TouchableOpacity>
            </View>
            <View style={{ width: 44 }} />
          </View>

          {/* Practice Mode Badge */}
          <View style={styles.practiceBadge}>
            <Ionicons name="shield-checkmark" size={16} color="#00BFFF" />
            <Text style={styles.practiceBadgeText}>PRACTICE MODE • NO HEARTS LOST</Text>
          </View>

          {mode === 'learn' ? (
            /* LEARN MODE */
            <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent}>
              <Text style={styles.lessonTitle}>{data?.title?.toUpperCase()}</Text>

              {/* Explanation */}
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>WHAT IS IT?</Text>
                <Text style={styles.explanationText}>{content?.explanation}</Text>
              </View>

              {/* Syntax */}
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>SYNTAX</Text>
                <View style={styles.codeBlock}>
                  <Text style={styles.codeText}>{content?.syntax}</Text>
                </View>
              </View>

              {/* Examples */}
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>EXAMPLES</Text>
                {content?.examples?.map((ex, idx) => (
                  <View key={idx} style={styles.exampleCard}>
                    <View style={styles.codeBlock}>
                      <Text style={styles.codeText}>{ex.code}</Text>
                    </View>
                    <View style={styles.outputBlock}>
                      <Ionicons name="arrow-forward" size={14} color="#00FF88" />
                      <Text style={styles.outputText}>{ex.output}</Text>
                    </View>
                  </View>
                ))}
              </View>

              {/* Tips */}
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>TIPS</Text>
                {content?.tips?.map((tip, idx) => (
                  <View key={idx} style={styles.tipRow}>
                    <Ionicons name="bulb" size={16} color="#FFD700" />
                    <Text style={styles.tipText}>{tip}</Text>
                  </View>
                ))}
              </View>

              {/* Common Mistakes */}
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>AVOID THESE MISTAKES</Text>
                {content?.common_mistakes?.map((mistake, idx) => (
                  <View key={idx} style={styles.mistakeRow}>
                    <Ionicons name="warning" size={16} color="#FF6B6B" />
                    <Text style={styles.mistakeText}>{mistake}</Text>
                  </View>
                ))}
              </View>

              <TouchableOpacity
                style={styles.startPracticeButton}
                onPress={() => setMode('practice')}
              >
                <LinearGradient colors={['#00BFFF', '#0080FF']} style={styles.startPracticeGradient}>
                  <Ionicons name="barbell" size={20} color="#FFF" />
                  <Text style={styles.startPracticeText}>START PRACTICING</Text>
                </LinearGradient>
              </TouchableOpacity>

              <View style={{ height: 40 }} />
            </ScrollView>
          ) : (
            /* PRACTICE MODE */
            <>
              <View style={styles.progressHeader}>
                <View style={styles.progressBar}>
                  <View
                    style={[
                      styles.progressFill,
                      { width: `${((currentExercise + 1) / (data?.exercises.length || 1)) * 100}%` },
                    ]}
                  />
                </View>
                <Text style={styles.progressText}>
                  {currentExercise + 1}/{data?.exercises.length}
                </Text>
              </View>

              <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent}>
                <Text style={styles.question}>{exercise?.question}</Text>

                {exercise?.type === 'multiple_choice' && exercise.options && (
                  <View style={styles.optionsContainer}>
                    {exercise.options.map((option, index) => (
                      <TouchableOpacity
                        key={index}
                        style={[
                          styles.optionButton,
                          selectedOption === index && styles.optionSelected,
                          showAnswer && index === exercise.correct && styles.optionCorrect,
                          showAnswer && selectedOption === index && index !== exercise.correct && styles.optionWrong,
                        ]}
                        onPress={() => !showAnswer && setSelectedOption(index)}
                      >
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

                {exercise?.type === 'code' && (
                  <>
                    <TextInput
                      style={styles.codeInput}
                      value={codeInput}
                      onChangeText={setCodeInput}
                      multiline
                      placeholder="WRITE YOUR CODE..."
                      placeholderTextColor="#555"
                      autoCapitalize="none"
                    />
                    {showAnswer && (
                      <View style={styles.solutionBox}>
                        <Text style={styles.solutionLabel}>SOLUTION:</Text>
                        <Text style={styles.solutionCode}>{exercise.solution}</Text>
                      </View>
                    )}
                  </>
                )}

                {exercise?.type === 'fill_blank' && (
                  <>
                    <TextInput
                      style={styles.fillInput}
                      value={fillInput}
                      onChangeText={setFillInput}
                      placeholder="YOUR ANSWER..."
                      placeholderTextColor="#555"
                      autoCapitalize="none"
                    />
                    {showAnswer && (
                      <View style={styles.solutionBox}>
                        <Text style={styles.solutionLabel}>ANSWER:</Text>
                        <Text style={styles.solutionCode}>{exercise.answer}</Text>
                      </View>
                    )}
                  </>
                )}

                {exercise?.explanation && showAnswer && (
                  <View style={styles.explanationBox}>
                    <Ionicons name="information-circle" size={18} color="#00BFFF" />
                    <Text style={styles.explanationBoxText}>{exercise.explanation}</Text>
                  </View>
                )}

                {!showAnswer && (
                  <TouchableOpacity
                    style={styles.showAnswerButton}
                    onPress={() => setShowAnswer(true)}
                  >
                    <Ionicons name="eye" size={18} color="#FFD700" />
                    <Text style={styles.showAnswerText}>SHOW ANSWER</Text>
                  </TouchableOpacity>
                )}
              </ScrollView>

              <View style={styles.footer}>
                <TouchableOpacity
                  style={styles.nextButton}
                  onPress={handleNext}
                  disabled={submitting}
                >
                  <LinearGradient colors={['#00BFFF', '#0080FF']} style={styles.nextGradient}>
                    {submitting ? (
                      <ActivityIndicator color="#FFF" />
                    ) : (
                      <Text style={styles.nextText}>
                        {currentExercise < (data?.exercises.length || 1) - 1 ? 'NEXT' : 'FINISH'}
                      </Text>
                    )}
                  </LinearGradient>
                </TouchableOpacity>
              </View>
            </>
          )}
        </KeyboardAvoidingView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#00BFFF', marginTop: 16 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16 },
  closeButton: {
    width: 44, height: 44, borderRadius: 12,
    backgroundColor: 'rgba(0, 191, 255, 0.1)', borderWidth: 1, borderColor: '#00BFFF',
    justifyContent: 'center', alignItems: 'center',
  },
  modeTabs: { flexDirection: 'row', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 8, padding: 4 },
  modeTab: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 6 },
  modeTabActive: { backgroundColor: '#00BFFF' },
  modeTabText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#888' },
  modeTabTextActive: { color: '#0D0D0D' },
  practiceBadge: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    backgroundColor: 'rgba(0, 191, 255, 0.1)', paddingVertical: 10, marginHorizontal: 16, borderRadius: 8,
  },
  practiceBadgeText: { fontFamily: 'PressStart2P_400Regular', fontSize: 7, color: '#00BFFF' },
  scroll: { flex: 1 },
  scrollContent: { padding: 16 },
  lessonTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 14, color: '#00BFFF', marginBottom: 20 },
  section: { marginBottom: 24 },
  sectionTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#FFD700', marginBottom: 12 },
  explanationText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#CCC', lineHeight: 18 },
  codeBlock: { backgroundColor: '#1a1a1a', borderRadius: 8, padding: 12, borderWidth: 1, borderColor: '#333' },
  codeText: { fontFamily: 'PressStart2P_400Regular', fontSize: 9, color: '#00FF88' },
  exampleCard: { marginBottom: 12 },
  outputBlock: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 8, paddingLeft: 12 },
  outputText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#00FF88' },
  tipRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, marginBottom: 8 },
  tipText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#CCC', flex: 1 },
  mistakeRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, marginBottom: 8 },
  mistakeText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#FF6B6B', flex: 1 },
  startPracticeButton: { borderRadius: 12, overflow: 'hidden', marginTop: 16 },
  startPracticeGradient: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 16, gap: 12 },
  startPracticeText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#FFF' },
  progressHeader: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 8, gap: 12 },
  progressBar: { flex: 1, height: 8, backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 4, overflow: 'hidden' },
  progressFill: { height: '100%', backgroundColor: '#00BFFF', borderRadius: 4 },
  progressText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#888' },
  question: { fontFamily: 'PressStart2P_400Regular', fontSize: 11, color: '#FFF', lineHeight: 22, marginBottom: 20 },
  optionsContainer: { gap: 10 },
  optionButton: {
    backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 12, padding: 16,
    borderWidth: 2, borderColor: 'rgba(255,255,255,0.1)',
  },
  optionSelected: { borderColor: '#00BFFF', backgroundColor: 'rgba(0, 191, 255, 0.1)' },
  optionCorrect: { borderColor: '#00FF88', backgroundColor: 'rgba(0, 255, 136, 0.1)' },
  optionWrong: { borderColor: '#FF6B6B', backgroundColor: 'rgba(255, 107, 107, 0.1)' },
  optionText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#AAA' },
  optionTextSelected: { color: '#FFF' },
  codeInput: {
    backgroundColor: '#1a1a1a', borderRadius: 12, padding: 16, minHeight: 120,
    fontFamily: 'PressStart2P_400Regular', fontSize: 9, color: '#00FF88', borderWidth: 1, borderColor: '#333',
  },
  fillInput: {
    backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 12, padding: 16,
    fontFamily: 'PressStart2P_400Regular', fontSize: 12, color: '#FFF', textAlign: 'center',
    borderWidth: 2, borderColor: 'rgba(0, 191, 255, 0.3)',
  },
  solutionBox: { backgroundColor: 'rgba(0, 255, 136, 0.1)', borderRadius: 8, padding: 12, marginTop: 12 },
  solutionLabel: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#00FF88', marginBottom: 8 },
  solutionCode: { fontFamily: 'PressStart2P_400Regular', fontSize: 9, color: '#00FF88' },
  explanationBox: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 10,
    backgroundColor: 'rgba(0, 191, 255, 0.1)', borderRadius: 8, padding: 12, marginTop: 16,
  },
  explanationBoxText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#00BFFF', flex: 1 },
  showAnswerButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: 20 },
  showAnswerText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#FFD700' },
  footer: { padding: 16 },
  nextButton: { borderRadius: 12, overflow: 'hidden' },
  nextGradient: { alignItems: 'center', justifyContent: 'center', paddingVertical: 16 },
  nextText: { fontFamily: 'PressStart2P_400Regular', fontSize: 12, color: '#FFF' },
  resultsContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  resultsIcon: {
    width: 120, height: 120, borderRadius: 60,
    backgroundColor: 'rgba(0, 191, 255, 0.1)', justifyContent: 'center', alignItems: 'center', marginBottom: 24,
  },
  resultsTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 16, color: '#00BFFF', marginBottom: 16 },
  resultsScore: { fontFamily: 'PressStart2P_400Regular', fontSize: 32, color: '#FFF', marginBottom: 8 },
  resultsDetail: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#888', marginBottom: 24 },
  practiceNote: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: 'rgba(0, 191, 255, 0.1)', paddingHorizontal: 16, paddingVertical: 10, borderRadius: 8, marginBottom: 16,
  },
  practiceNoteText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#00BFFF' },
  practiceMessage: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#888', textAlign: 'center', marginBottom: 32 },
  resultsButtons: { width: '100%', gap: 12 },
  retryButton: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10,
    backgroundColor: 'rgba(0, 191, 255, 0.1)', borderRadius: 12, paddingVertical: 14,
    borderWidth: 1, borderColor: '#00BFFF',
  },
  retryText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#00BFFF' },
  lessonButton: { borderRadius: 12, overflow: 'hidden' },
  lessonGradient: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 16, gap: 12 },
  lessonText: { fontFamily: 'PressStart2P_400Regular', fontSize: 12, color: '#0D0D0D' },
});
