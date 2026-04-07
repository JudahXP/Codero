import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../src/services/api';
import { useAuth } from '../src/context/AuthContext';

interface LeaderboardUser {
  username: string;
  xp: number;
  level: number;
  streak: number;
  badges_count: number;
}

export default function LeaderboardScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const [leaderboard, setLeaderboard] = useState<LeaderboardUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    try {
      const response = await api.get('/leaderboard');
      setLeaderboard(response.data);
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchLeaderboard();
    setRefreshing(false);
  };

  const getRankColor = (index: number) => {
    switch (index) {
      case 0:
        return '#FFD700';
      case 1:
        return '#C0C0C0';
      case 2:
        return '#CD7F32';
      default:
        return '#555';
    }
  };

  const getRankIcon = (index: number) => {
    if (index < 3) return 'trophy';
    return 'medal';
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
            <Text style={styles.title}>LEADERBOARD</Text>
            <Text style={styles.subtitle}>TOP CODERS</Text>
          </View>
        </View>

        {/* Top 3 Podium */}
        {leaderboard.length >= 3 && (
          <View style={styles.podiumContainer}>
            {/* 2nd Place */}
            <View style={styles.podiumSpot}>
              <View style={[styles.podiumAvatar, { backgroundColor: 'rgba(192, 192, 192, 0.2)' }]}>
                <Ionicons name="person" size={28} color="#C0C0C0" />
              </View>
              <Text style={styles.podiumName}>{leaderboard[1].username.substring(0, 6).toUpperCase()}</Text>
              <Text style={[styles.podiumXp, { color: '#C0C0C0' }]}>{leaderboard[1].xp} XP</Text>
              <View style={[styles.podiumBar, { height: 60, backgroundColor: '#C0C0C0' }]}>
                <Text style={styles.podiumRank}>2</Text>
              </View>
            </View>

            {/* 1st Place */}
            <View style={styles.podiumSpot}>
              <View style={[styles.podiumAvatar, { backgroundColor: 'rgba(255, 215, 0, 0.2)' }]}>
                <Ionicons name="person" size={32} color="#FFD700" />
              </View>
              <Text style={styles.podiumName}>{leaderboard[0].username.substring(0, 6).toUpperCase()}</Text>
              <Text style={[styles.podiumXp, { color: '#FFD700' }]}>{leaderboard[0].xp} XP</Text>
              <View style={[styles.podiumBar, { height: 80, backgroundColor: '#FFD700' }]}>
                <Text style={styles.podiumRank}>1</Text>
              </View>
            </View>

            {/* 3rd Place */}
            <View style={styles.podiumSpot}>
              <View style={[styles.podiumAvatar, { backgroundColor: 'rgba(205, 127, 50, 0.2)' }]}>
                <Ionicons name="person" size={28} color="#CD7F32" />
              </View>
              <Text style={styles.podiumName}>{leaderboard[2].username.substring(0, 6).toUpperCase()}</Text>
              <Text style={[styles.podiumXp, { color: '#CD7F32' }]}>{leaderboard[2].xp} XP</Text>
              <View style={[styles.podiumBar, { height: 40, backgroundColor: '#CD7F32' }]}>
                <Text style={styles.podiumRank}>3</Text>
              </View>
            </View>
          </View>
        )}

        {/* Rankings List */}
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.scrollContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#00FF88" />
          }
        >
          {leaderboard.slice(3).map((entry, index) => {
            const rank = index + 4;
            const isCurrentUser = entry.username === user?.username;

            return (
              <View
                key={entry.username}
                style={[
                  styles.rankCard,
                  isCurrentUser && styles.rankCardCurrent,
                ]}
              >
                <View style={styles.rankLeft}>
                  <Text style={styles.rankNumber}>#{rank}</Text>
                  <View style={styles.rankAvatar}>
                    <Ionicons name="person" size={20} color="#888" />
                  </View>
                  <View style={styles.rankInfo}>
                    <Text style={[
                      styles.rankName,
                      isCurrentUser && styles.rankNameCurrent
                    ]}>
                      {entry.username.toUpperCase()}
                    </Text>
                    <Text style={styles.rankLevel}>LV{entry.level}</Text>
                  </View>
                </View>
                <View style={styles.rankRight}>
                  <View style={styles.rankStat}>
                    <Ionicons name="star" size={14} color="#FFD700" />
                    <Text style={styles.rankStatValue}>{entry.xp}</Text>
                  </View>
                  <View style={styles.rankStat}>
                    <Ionicons name="flame" size={14} color="#FF6B6B" />
                    <Text style={styles.rankStatValue}>{entry.streak}</Text>
                  </View>
                </View>
              </View>
            );
          })}
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
    fontSize: 14,
    color: '#FFD700',
  },
  subtitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#888',
    marginTop: 4,
  },
  podiumContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'flex-end',
    paddingHorizontal: 20,
    paddingBottom: 20,
    gap: 8,
  },
  podiumSpot: {
    alignItems: 'center',
    flex: 1,
  },
  podiumAvatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  podiumName: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 7,
    color: '#FFF',
    marginBottom: 4,
  },
  podiumXp: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    marginBottom: 8,
  },
  podiumBar: {
    width: '100%',
    borderTopLeftRadius: 8,
    borderTopRightRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  podiumRank: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 16,
    color: '#0D0D0D',
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    gap: 10,
  },
  rankCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  rankCardCurrent: {
    borderColor: '#00FF88',
    backgroundColor: 'rgba(0, 255, 136, 0.1)',
  },
  rankLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  rankNumber: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#555',
    width: 36,
  },
  rankAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  rankInfo: {
    flex: 1,
  },
  rankName: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 9,
    color: '#FFF',
  },
  rankNameCurrent: {
    color: '#00FF88',
  },
  rankLevel: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 7,
    color: '#888',
    marginTop: 2,
  },
  rankRight: {
    flexDirection: 'row',
    gap: 16,
  },
  rankStat: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  rankStatValue: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#FFF',
  },
  bottomPadding: {
    height: 40,
  },
});
