import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../src/context/AuthContext';
import { api } from '../src/services/api';

interface Language {
  id: string;
  name: string;
  icon: string;
  color: string;
  description: string;
}

export default function HomeScreen() {
  const router = useRouter();
  const { user, refreshUser } = useAuth();
  const [languages, setLanguages] = useState<Language[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [continueLearning, setContinueLearning] = useState<any>(null);


  useEffect(() => {
    fetchLanguages();
    fetchContinueLearning();
  }, []);

  const fetchContinueLearning = async () => {
    try {
      const response = await api.get('/continue-learning');
      setContinueLearning(response.data);
    } catch (error) {
      console.error('Failed to fetch continue learning:', error);
    }
  };

  const fetchLanguages = async () => {
    try {
      const response = await api.get('/languages');
      setLanguages(response.data);
    } catch (error) {
      console.error('Failed to fetch languages:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([fetchLanguages(), fetchContinueLearning(), refreshUser()]);
    setRefreshing(false);
  };

  const getXPForNextLevel = () => {
    return (user?.level || 1) * 100;
  };

  const getCurrentLevelXP = () => {
    const totalXP = user?.xp || 0;
    const level = user?.level || 1;
    const xpForCurrentLevel = (level - 1) * 100;
    return totalXP - xpForCurrentLevel;
  };

  return (
    <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>HI, {user?.username?.toUpperCase() || 'CODER'}!</Text>
            <Text style={styles.subGreeting}>READY TO CODE?</Text>
          </View>
          <View style={styles.headerRight}>
            <TouchableOpacity style={styles.headerButton} onPress={() => router.push('/profile')}>
              <Ionicons name="person" size={20} color="#00FF88" />
            </TouchableOpacity>
          </View>
        </View>

        {/* Stats Bar */}
        <View style={styles.statsBar}>
          <View style={styles.statItem}>
            <Ionicons name="flame" size={18} color="#FF6B6B" />
            <Text style={styles.statValue}>{user?.streak || 0}</Text>
          </View>
          <View style={styles.statItem}>
            <Ionicons name="star" size={18} color="#FFD700" />
            <Text style={styles.statValue}>{user?.xp || 0}</Text>
          </View>
          <View style={styles.statItem}>
            <Ionicons name="heart" size={18} color="#FF6B6B" />
            <Text style={styles.statValue}>{user?.hearts || 5}</Text>
          </View>
          <View style={styles.statItem}>
            <Ionicons name="trophy" size={18} color="#00FF88" />
            <Text style={styles.statValue}>LV{user?.level || 1}</Text>
          </View>
        </View>

        {/* XP Progress */}
        <View style={styles.xpContainer}>
          <View style={styles.xpHeader}>
            <Text style={styles.xpLabel}>LEVEL {user?.level || 1}</Text>
            <Text style={styles.xpText}>{getCurrentLevelXP()}/{getXPForNextLevel()} XP</Text>
          </View>
          <View style={styles.xpBar}>
            <View
              style={[
                styles.xpProgress,
                { width: `${Math.min((getCurrentLevelXP() / getXPForNextLevel()) * 100, 100)}%` },
              ]}
            />
          </View>
        </View>

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <TouchableOpacity style={styles.actionButton} onPress={() => router.push('/daily-challenge')}>
            <LinearGradient colors={['#FFD700', '#FFA500']} style={styles.actionGradient}>
              <Ionicons name="flash" size={24} color="#0D0D0D" />
            </LinearGradient>
            <Text style={styles.actionText}>DAILY</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton} onPress={() => router.push('/games')}>
            <LinearGradient colors={['#FF6B6B', '#FF4757']} style={styles.actionGradient}>
              <Ionicons name="game-controller" size={24} color="#0D0D0D" />
            </LinearGradient>
            <Text style={styles.actionText}>GAMES</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton} onPress={() => router.push('/leaderboard')}>
            <LinearGradient colors={['#00BFFF', '#0080FF']} style={styles.actionGradient}>
              <Ionicons name="podium" size={24} color="#0D0D0D" />
            </LinearGradient>
            <Text style={styles.actionText}>RANKS</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton} onPress={() => router.push('/vip')}>
            <LinearGradient colors={['#FFD700', '#FF8C00']} style={styles.actionGradient}>
              <Ionicons name="star" size={24} color="#0D0D0D" />
            </LinearGradient>
            <Text style={styles.actionText}>VIP</Text>
          </TouchableOpacity>
        </View>

        {/* Continue Learning */}
        {continueLearning?.has_continue && (
          <TouchableOpacity
            style={styles.continueLearningCard}
            onPress={() => router.push(`/lesson/${continueLearning.language_id}/${continueLearning.lesson_id}`)}
            activeOpacity={0.85}
          >
            <LinearGradient colors={['rgba(0,255,136,0.22)', 'rgba(0,191,255,0.14)']} style={styles.continueLearningGradient}>
              <View style={styles.continueLearningIcon}>
                <Ionicons name="play" size={22} color="#0D0D0D" />
              </View>
              <View style={styles.continueLearningTextWrap}>
                <Text style={styles.continueLearningLabel}>CONTINUE LEARNING</Text>
                <Text style={styles.continueLearningTitle}>{String(continueLearning.title || '').toUpperCase()}</Text>
                <Text style={styles.continueLearningMeta}>{continueLearning.completed_lessons}/{continueLearning.total_lessons} LESSONS DONE</Text>
              </View>
              <Ionicons name="chevron-forward" size={24} color="#00FF88" />
            </LinearGradient>
          </TouchableOpacity>
        )}

        {/* Languages */}
        <View style={styles.languagesHeader}>
          <Text style={styles.sectionTitle}>CHOOSE LANGUAGE</Text>
          <Text style={styles.sectionCount}>{languages.length} AVAILABLE</Text>
        </View>

        <ScrollView
          style={styles.languagesScroll}
          contentContainerStyle={styles.languagesContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#00FF88" />
          }
          showsVerticalScrollIndicator={false}
        >
          {languages.map((lang) => (
            <TouchableOpacity
              key={lang.id}
              style={styles.languageCard}
              onPress={() => router.push(`/language/${lang.id}`)}
              activeOpacity={0.8}
            >
              <View style={[styles.languageIcon, { backgroundColor: `${lang.color}20` }]}>
                <Ionicons name={lang.icon as any} size={28} color={lang.color} />
              </View>
              <View style={styles.languageInfo}>
                <Text style={styles.languageName}>{lang.name.toUpperCase()}</Text>
                <Text style={styles.languageDesc}>{lang.description.toUpperCase()}</Text>
              </View>
              <Ionicons name="chevron-forward" size={24} color="#00FF88" />
            </TouchableOpacity>
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 16,
  },
  greeting: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 14,
    color: '#00FF88',
  },
  subGreeting: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#888888',
    marginTop: 4,
  },
  headerRight: {
    flexDirection: 'row',
    gap: 12,
  },
  headerButton: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: 'rgba(0, 255, 136, 0.1)',
    borderWidth: 1,
    borderColor: '#00FF88',
    justifyContent: 'center',
    alignItems: 'center',
  },
  statsBar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 20,
    paddingVertical: 12,
    marginHorizontal: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  statValue: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#FFFFFF',
  },
  xpContainer: {
    marginHorizontal: 20,
    marginTop: 16,
  },
  xpHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  xpLabel: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#00FF88',
  },
  continueLearningCard: {
    marginHorizontal: 20,
    marginBottom: 18,
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(0, 255, 136, 0.35)',
  },
  continueLearningGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    padding: 16,
  },
  continueLearningIcon: {
    width: 48,
    height: 48,
    borderRadius: 14,
    backgroundColor: '#00FF88',
    alignItems: 'center',
    justifyContent: 'center',
  },
  continueLearningTextWrap: {
    flex: 1,
    gap: 6,
  },
  continueLearningLabel: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 7,
    color: '#00FF88',
  },
  continueLearningTitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#FFF',
    lineHeight: 18,
  },
  continueLearningMeta: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 7,
    color: '#888',
  },
  xpText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#888888',
  },
  xpBar: {
    height: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 4,
    overflow: 'hidden',
  },
  xpProgress: {
    height: '100%',
    backgroundColor: '#00FF88',
    borderRadius: 4,
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 24,
    paddingVertical: 20,
  },
  actionButton: {
    alignItems: 'center',
    gap: 8,
  },
  actionGradient: {
    width: 56,
    height: 56,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  actionText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 7,
    color: '#FFFFFF',
  },
  languagesHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  sectionTitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#FFFFFF',
  },
  sectionCount: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#00FF88',
  },
  languagesScroll: {
    flex: 1,
  },
  languagesContent: {
    paddingHorizontal: 20,
    gap: 12,
  },
  languageCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  languageIcon: {
    width: 56,
    height: 56,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  languageInfo: {
    flex: 1,
    marginLeft: 16,
  },
  languageName: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 11,
    color: '#FFFFFF',
    marginBottom: 4,
  },
  languageDesc: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 6,
    color: '#888888',
  },
  bottomPadding: {
    height: 20,
  },
});
