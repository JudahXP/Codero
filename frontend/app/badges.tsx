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
import { api } from '../src/services/api';
import { useAuth } from '../src/context/AuthContext';

interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export default function BadgesScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const [badges, setBadges] = useState<Badge[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBadges();
  }, []);

  const fetchBadges = async () => {
    try {
      const response = await api.get('/badges');
      setBadges(response.data);
    } catch (error) {
      console.error('Failed to fetch badges:', error);
    } finally {
      setLoading(false);
    }
  };

  const userBadges = user?.badges || [];

  const getBadgeColor = (badgeId: string) => {
    if (badgeId.includes('xp')) return '#FFD700';
    if (badgeId.includes('streak')) return '#FF6B6B';
    if (badgeId.includes('social')) return '#00FF88';
    return '#00BFFF';
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
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={24} color="#00FF88" />
          </TouchableOpacity>
          <View style={styles.headerInfo}>
            <Text style={styles.title}>BADGES</Text>
            <Text style={styles.subtitle}>
              {userBadges.length}/{badges.length} UNLOCKED
            </Text>
          </View>
        </View>

        {/* Progress */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View
              style={[
                styles.progressFill,
                { width: `${badges.length > 0 ? (userBadges.length / badges.length) * 100 : 0}%` },
              ]}
            />
          </View>
        </View>

        {/* Badges Grid */}
        <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent}>
          <View style={styles.badgesGrid}>
            {badges.map((badge) => {
              const unlocked = userBadges.includes(badge.id);
              const color = getBadgeColor(badge.id);

              return (
                <View
                  key={badge.id}
                  style={[
                    styles.badgeCard,
                    unlocked && styles.badgeCardUnlocked,
                    unlocked && { borderColor: color },
                  ]}
                >
                  <View style={[
                    styles.badgeIcon,
                    { backgroundColor: unlocked ? `${color}20` : 'rgba(255,255,255,0.05)' }
                  ]}>
                    <Ionicons
                      name={badge.icon as any}
                      size={32}
                      color={unlocked ? color : '#444'}
                    />
                    {!unlocked && (
                      <View style={styles.lockOverlay}>
                        <Ionicons name="lock-closed" size={16} color="#666" />
                      </View>
                    )}
                  </View>
                  <Text style={[
                    styles.badgeName,
                    unlocked && { color: '#FFF' }
                  ]}>
                    {badge.name.toUpperCase()}
                  </Text>
                  <Text style={styles.badgeDesc}>
                    {badge.description.toUpperCase()}
                  </Text>
                </View>
              );
            })}
          </View>
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
  title: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 16,
    color: '#FF6B6B',
  },
  subtitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#888',
    marginTop: 4,
  },
  progressContainer: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  progressBar: {
    height: 8,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#FF6B6B',
    borderRadius: 4,
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
  },
  badgesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  badgeCard: {
    width: '47%',
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  badgeCardUnlocked: {
    backgroundColor: 'rgba(255,255,255,0.05)',
  },
  badgeIcon: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  lockOverlay: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#1a1a1a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  badgeName: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#666',
    textAlign: 'center',
    marginBottom: 4,
  },
  badgeDesc: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 6,
    color: '#555',
    textAlign: 'center',
  },
  bottomPadding: {
    height: 40,
  },
});
