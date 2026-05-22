import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/services/api';
import { safeBack } from '../../src/utils/navigation';

interface Lesson {
  id: string;
  title: string;
  description: string;
  xp: number;
  unit: number;
  unit_name?: string;
  completed: boolean;
  has_practice?: boolean;
}

interface Progress {
  total_lessons: number;
  completed_lessons: number;
  progress_percent: number;
}

const LANGUAGE_COLORS: Record<string, string> = {
  python: '#3776AB',
  javascript: '#F7DF1E',
  java: '#ED8B00',
  cpp: '#00599C',
  csharp: '#239120',
  ruby: '#CC342D',
  go: '#00ADD8',
  rust: '#DEA584',
  swift: '#FA7343',
  kotlin: '#7F52FF',
  typescript: '#3178C6',
  php: '#777BB4',
  sql: '#4479A1',
  html_css: '#E34F26',
  skript: '#6B8E23',
  lua: '#000080',
};

export default function LanguageScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [loading, setLoading] = useState(true);

  const color = LANGUAGE_COLORS[id || ''] || '#00FF88';

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      const [lessonsRes, progressRes] = await Promise.all([
        api.get(`/languages/${id}/lessons`),
        api.get(`/progress/${id}`),
      ]);
      setLessons(lessonsRes.data);
      setProgress(progressRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Group lessons by unit
  const unitGroups = lessons.reduce((acc, lesson) => {
    const unit = lesson.unit;
    if (!acc[unit]) acc[unit] = [];
    acc[unit].push(lesson);
    return acc;
  }, {} as Record<number, Lesson[]>);

  const unitNames: Record<number, string> = {
    1: 'BASICS',
    2: 'CONTROL FLOW',
    3: 'FUNCTIONS',
    4: 'DATA STRUCTURES',
    5: 'OOP',
    6: 'ADVANCED',
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

  return (
    <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => safeBack(router, '/home')}>
            <Ionicons name="arrow-back" size={24} color="#00FF88" />
          </TouchableOpacity>
          <View style={styles.headerInfo}>
            <Text style={[styles.languageName, { color }]}>{id?.toUpperCase()}</Text>
            <Text style={styles.lessonCount}>
              {progress?.completed_lessons || 0}/{progress?.total_lessons || 0} LESSONS
            </Text>
          </View>
        </View>

        {/* Progress Bar */}
        <View style={styles.progressContainer}>
          <View style={styles.progressHeader}>
            <Text style={styles.progressLabel}>PROGRESS</Text>
            <Text style={styles.progressPercent}>{progress?.progress_percent || 0}%</Text>
          </View>
          <View style={styles.progressBar}>
            <View
              style={[
                styles.progressFill,
                { width: `${progress?.progress_percent || 0}%`, backgroundColor: color },
              ]}
            />
          </View>
        </View>

        {/* Lessons */}
        <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent}>
          {Object.entries(unitGroups).map(([unit, unitLessons]) => (
            <View key={unit} style={styles.unitSection}>
              <View style={styles.unitHeader}>
                <View style={[styles.unitBadge, { backgroundColor: `${color}30` }]}>
                  <Text style={[styles.unitNumber, { color }]}>UNIT {unit}</Text>
                </View>
                <Text style={styles.unitName}>{unitNames[Number(unit)] || `UNIT ${unit}`}</Text>
              </View>

              <View style={styles.lessonsGrid}>
                {unitLessons.map((lesson, index) => {
                  const isLocked = index > 0 && !unitLessons[index - 1].completed;
                  const isFirst = index === 0;
                  const prevUnitCompleted = Number(unit) === 1 || 
                    (unitGroups[Number(unit) - 1]?.every(l => l.completed));
                  const actuallyLocked = isFirst ? !prevUnitCompleted && Number(unit) > 1 : isLocked;

                  return (
                    <View key={lesson.id} style={styles.lessonRow}>
                      <TouchableOpacity
                        style={[
                          styles.lessonCard,
                          lesson.completed && styles.lessonCompleted,
                          actuallyLocked && styles.lessonLocked,
                        ]}
                        onPress={() => {
                          if (!actuallyLocked) {
                            router.push(`/lesson/${id}/${lesson.id}`);
                          }
                        }}
                        activeOpacity={actuallyLocked ? 1 : 0.7}
                      >
                        <View style={styles.lessonLeft}>
                          {lesson.completed ? (
                            <View style={[styles.lessonIcon, { backgroundColor: `${color}30` }]}>
                              <Ionicons name="checkmark" size={20} color={color} />
                            </View>
                          ) : actuallyLocked ? (
                            <View style={[styles.lessonIcon, { backgroundColor: 'rgba(255,255,255,0.05)' }]}>
                              <Ionicons name="lock-closed" size={20} color="#666" />
                            </View>
                          ) : (
                            <View style={[styles.lessonIcon, { backgroundColor: `${color}20` }]}>
                              <Ionicons name="play" size={20} color={color} />
                            </View>
                          )}
                          <View style={styles.lessonInfo}>
                            <Text style={[
                              styles.lessonTitle,
                              actuallyLocked && styles.lessonTitleLocked
                            ]}>
                              {lesson.title.toUpperCase()}
                            </Text>
                            <Text style={styles.lessonXp}>+{lesson.xp} XP</Text>
                          </View>
                        </View>
                        <Ionicons
                          name="chevron-forward"
                          size={20}
                          color={actuallyLocked ? '#444' : '#00FF88'}
                        />
                      </TouchableOpacity>
                      {!actuallyLocked && (
                        <TouchableOpacity
                          style={styles.practiceButton}
                          onPress={() => router.push(`/practice/${id}/${lesson.id}`)}
                        >
                          <Ionicons name="school" size={16} color="#00BFFF" />
                        </TouchableOpacity>
                      )}
                    </View>
                  );
                })}
              </View>
            </View>
          ))}
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
    gap: 16,
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
  headerInfo: {
    flex: 1,
  },
  languageName: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 16,
  },
  lessonCount: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#888',
    marginTop: 4,
  },
  progressContainer: {
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  progressLabel: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#888',
  },
  progressPercent: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#00FF88',
  },
  progressBar: {
    height: 8,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
  },
  unitSection: {
    marginBottom: 24,
  },
  unitHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  unitBadge: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  unitNumber: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
  },
  unitName: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#FFF',
  },
  lessonsGrid: {
    gap: 10,
  },
  lessonRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  lessonCard: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(0, 255, 136, 0.2)',
  },
  practiceButton: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: 'rgba(0, 191, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(0, 191, 255, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  lessonCompleted: {
    borderColor: 'rgba(0, 255, 136, 0.5)',
  },
  lessonLocked: {
    opacity: 0.5,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  lessonLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  lessonIcon: {
    width: 40,
    height: 40,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  lessonInfo: {
    marginLeft: 12,
    flex: 1,
  },
  lessonTitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 9,
    color: '#FFF',
  },
  lessonTitleLocked: {
    color: '#666',
  },
  lessonXp: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 7,
    color: '#FFD700',
    marginTop: 4,
  },
  bottomPadding: {
    height: 40,
  },
});
