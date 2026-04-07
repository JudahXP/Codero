import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../src/context/AuthContext';

export default function ProfileScreen() {
  const router = useRouter();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    Alert.alert(
      'LOGOUT',
      'Are you sure you want to logout?',
      [
        { text: 'CANCEL', style: 'cancel' },
        {
          text: 'LOGOUT',
          style: 'destructive',
          onPress: async () => {
            await logout();
            router.replace('/');
          },
        },
      ]
    );
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
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={24} color="#00FF88" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>PROFILE</Text>
          <View style={{ width: 44 }} />
        </View>

        <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent}>
          {/* Avatar Section */}
          <View style={styles.avatarSection}>
            <View style={styles.avatarContainer}>
              <Ionicons name="person" size={48} color="#00FF88" />
            </View>
            <Text style={styles.username}>{user?.username?.toUpperCase() || 'CODER'}</Text>
            <Text style={styles.email}>{user?.email}</Text>
          </View>

          {/* Level Progress */}
          <View style={styles.levelContainer}>
            <View style={styles.levelHeader}>
              <View style={styles.levelBadge}>
                <Ionicons name="trophy" size={18} color="#FFD700" />
                <Text style={styles.levelText}>LEVEL {user?.level || 1}</Text>
              </View>
              <Text style={styles.xpText}>
                {getCurrentLevelXP()}/{getXPForNextLevel()} XP
              </Text>
            </View>
            <View style={styles.levelBar}>
              <View
                style={[
                  styles.levelProgress,
                  { width: `${Math.min((getCurrentLevelXP() / getXPForNextLevel()) * 100, 100)}%` },
                ]}
              />
            </View>
          </View>

          {/* Stats Grid */}
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Ionicons name="star" size={28} color="#FFD700" />
              <Text style={styles.statValue}>{user?.xp || 0}</Text>
              <Text style={styles.statLabel}>TOTAL XP</Text>
            </View>
            <View style={styles.statCard}>
              <Ionicons name="flame" size={28} color="#FF6B6B" />
              <Text style={styles.statValue}>{user?.streak || 0}</Text>
              <Text style={styles.statLabel}>DAY STREAK</Text>
            </View>
            <View style={styles.statCard}>
              <Ionicons name="heart" size={28} color="#FF6B6B" />
              <Text style={styles.statValue}>{user?.hearts || 5}</Text>
              <Text style={styles.statLabel}>HEARTS</Text>
            </View>
            <View style={styles.statCard}>
              <Ionicons name="diamond" size={28} color="#00BFFF" />
              <Text style={styles.statValue}>{user?.gems || 0}</Text>
              <Text style={styles.statLabel}>GEMS</Text>
            </View>
          </View>

          {/* Menu Items */}
          <View style={styles.menuSection}>
            <TouchableOpacity
              style={styles.menuItem}
              onPress={() => router.push('/settings')}
            >
              <View style={styles.menuLeft}>
                <View style={[styles.menuIcon, { backgroundColor: 'rgba(0, 191, 255, 0.1)' }]}>
                  <Ionicons name="settings" size={22} color="#00BFFF" />
                </View>
                <Text style={styles.menuText}>SETTINGS</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#555" />
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.menuItem}
              onPress={() => router.push('/badges')}
            >
              <View style={styles.menuLeft}>
                <View style={[styles.menuIcon, { backgroundColor: 'rgba(255, 107, 107, 0.1)' }]}>
                  <Ionicons name="medal" size={22} color="#FF6B6B" />
                </View>
                <Text style={styles.menuText}>VIEW BADGES</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#555" />
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.menuItem}
              onPress={() => router.push('/friends')}
            >
              <View style={styles.menuLeft}>
                <View style={[styles.menuIcon, { backgroundColor: 'rgba(0, 255, 136, 0.1)' }]}>
                  <Ionicons name="people" size={22} color="#00FF88" />
                </View>
                <Text style={styles.menuText}>FRIENDS</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#555" />
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.menuItem}
              onPress={() => router.push('/leaderboard')}
            >
              <View style={styles.menuLeft}>
                <View style={[styles.menuIcon, { backgroundColor: 'rgba(255, 215, 0, 0.1)' }]}>
                  <Ionicons name="podium" size={22} color="#FFD700" />
                </View>
                <Text style={styles.menuText}>LEADERBOARD</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color="#555" />
            </TouchableOpacity>
          </View>

          {/* Logout Button */}
          <TouchableOpacity
            style={styles.logoutButton}
            onPress={handleLogout}
          >
            <Ionicons name="log-out" size={20} color="#FF6B6B" />
            <Text style={styles.logoutText}>LOGOUT</Text>
          </TouchableOpacity>

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
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 20,
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
  headerTitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 14,
    color: '#00FF88',
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
  },
  avatarSection: {
    alignItems: 'center',
    marginBottom: 24,
  },
  avatarContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(0, 255, 136, 0.1)',
    borderWidth: 3,
    borderColor: '#00FF88',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  username: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 16,
    color: '#FFF',
    marginBottom: 8,
  },
  email: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 7,
    color: '#888',
  },
  levelContainer: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.2)',
  },
  levelHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  levelBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  levelText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#FFD700',
  },
  xpText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#888',
  },
  levelBar: {
    height: 10,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 5,
    overflow: 'hidden',
  },
  levelProgress: {
    height: '100%',
    backgroundColor: '#FFD700',
    borderRadius: 5,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 24,
  },
  statCard: {
    width: '47%',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  statValue: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 18,
    color: '#FFF',
    marginVertical: 8,
  },
  statLabel: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 7,
    color: '#888',
  },
  menuSection: {
    gap: 12,
    marginBottom: 24,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  menuLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  menuIcon: {
    width: 40,
    height: 40,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  menuText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 9,
    color: '#FFF',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    backgroundColor: 'rgba(255, 107, 107, 0.1)',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 107, 0.3)',
  },
  logoutText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#FF6B6B',
  },
  bottomPadding: {
    height: 40,
  },
});
