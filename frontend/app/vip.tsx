import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../src/services/api';
import { useAuth } from '../src/context/AuthContext';

interface Perk {
  icon: string;
  title: string;
  description: string;
}

export default function VIPScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const [vipInfo, setVipInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const streak = user?.streak || 0;
  const isVIP = streak >= 7;
  const progress = Math.min(streak / 7, 1);

  useEffect(() => {
    fetchVIPInfo();
  }, []);

  const fetchVIPInfo = async () => {
    try {
      const res = await api.get('/vip/info');
      setVipInfo(res.data);
    } catch (e) {
      console.error('VIP info error:', e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#FFD700" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.header}>
          <Pressable style={styles.backButton} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={24} color="#FFD700" />
          </Pressable>
          <Text style={styles.headerTitle}>VIP STATUS</Text>
          <View style={{ width: 44 }} />
        </View>

        <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          {/* VIP Badge */}
          <View style={styles.badgeSection}>
            <View style={[styles.bigBadge, isVIP && styles.bigBadgeActive]}>
              <Ionicons name="star" size={50} color={isVIP ? '#FFD700' : '#555'} />
            </View>
            <Text style={[styles.statusText, isVIP && { color: '#FFD700' }]}>
              {isVIP ? 'VIP ACTIVE!' : 'NOT VIP YET'}
            </Text>
            <Text style={styles.statusDesc}>
              {isVIP
                ? 'KEEP YOUR STREAK TO STAY VIP!'
                : `REACH A 7-DAY STREAK TO UNLOCK VIP`}
            </Text>
          </View>

          {/* Streak Progress */}
          <View style={styles.progressSection}>
            <View style={styles.progressHeader}>
              <Ionicons name="flame" size={18} color="#FF6B6B" />
              <Text style={styles.progressLabel}>STREAK: {streak} / 7 DAYS</Text>
            </View>
            <View style={styles.progressBar}>
              <View style={[styles.progressFill, { width: `${progress * 100}%` }]} />
            </View>
            <View style={styles.daysRow}>
              {[1, 2, 3, 4, 5, 6, 7].map(day => (
                <View key={day} style={[styles.dayDot, streak >= day && styles.dayDotActive]}>
                  <Text style={[styles.dayText, streak >= day && styles.dayTextActive]}>{day}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* Perks */}
          <Text style={styles.perksTitle}>VIP PERKS</Text>
          {vipInfo?.perks?.map((perk: Perk, i: number) => (
            <View key={i} style={[styles.perkCard, !isVIP && styles.perkLocked]}>
              <View style={[styles.perkIcon, isVIP && { backgroundColor: 'rgba(255,215,0,0.15)' }]}>
                <Ionicons name={perk.icon as any} size={22} color={isVIP ? '#FFD700' : '#555'} />
              </View>
              <View style={styles.perkInfo}>
                <Text style={[styles.perkTitle, !isVIP && { color: '#666' }]}>{perk.title}</Text>
                <Text style={styles.perkDesc}>{perk.description}</Text>
              </View>
              {isVIP ? (
                <Ionicons name="checkmark-circle" size={20} color="#00FF88" />
              ) : (
                <Ionicons name="lock-closed" size={20} color="#555" />
              )}
            </View>
          ))}

          {/* How to earn */}
          <View style={styles.howToSection}>
            <Text style={styles.howToTitle}>HOW TO EARN VIP</Text>
            <View style={styles.howToStep}>
              <View style={styles.stepNum}><Text style={styles.stepNumText}>1</Text></View>
              <Text style={styles.stepText}>COMPLETE AT LEAST ONE LESSON OR GAME DAILY</Text>
            </View>
            <View style={styles.howToStep}>
              <View style={styles.stepNum}><Text style={styles.stepNumText}>2</Text></View>
              <Text style={styles.stepText}>MAINTAIN YOUR STREAK FOR 7 DAYS</Text>
            </View>
            <View style={styles.howToStep}>
              <View style={styles.stepNum}><Text style={styles.stepNumText}>3</Text></View>
              <Text style={styles.stepText}>VIP STAYS ACTIVE AS LONG AS YOUR STREAK IS 7+</Text>
            </View>
          </View>

          <View style={{ height: 40 }} />
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0D0D0D' },
  safeArea: { flex: 1 },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0D0D0D' },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16,
  },
  backButton: {
    width: 44, height: 44, borderRadius: 12,
    backgroundColor: 'rgba(255,215,0,0.1)', borderWidth: 0, borderColor: '#FFD700',
    justifyContent: 'center', alignItems: 'center',
  },
  headerTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 12, color: '#FFD700' },
  scroll: { flex: 1 },
  scrollContent: { paddingHorizontal: 20 },
  badgeSection: { alignItems: 'center', paddingVertical: 24 },
  bigBadge: {
    width: 100, height: 100, borderRadius: 50,
    backgroundColor: 'rgba(85,85,85,0.2)', borderWidth: 0, borderColor: '#333',
    justifyContent: 'center', alignItems: 'center', marginBottom: 16,
  },
  bigBadgeActive: { backgroundColor: 'rgba(255,215,0,0.15)', borderColor: '#FFD700' },
  statusText: { fontFamily: 'PressStart2P_400Regular', fontSize: 16, color: '#888', marginBottom: 8 },
  statusDesc: { fontFamily: 'PressStart2P_400Regular', fontSize: 7, color: '#888', textAlign: 'center', lineHeight: 14 },
  progressSection: {
    backgroundColor: 'rgba(255,255,255,0.04)', borderRadius: 16, padding: 16, marginBottom: 24,
    borderWidth: 0, borderColor: 'rgba(255,255,255,0.08)',
  },
  progressHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  progressLabel: { fontFamily: 'PressStart2P_400Regular', fontSize: 9, color: '#FFF' },
  progressBar: { height: 10, backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 5, overflow: 'hidden', marginBottom: 12 },
  progressFill: { height: '100%', backgroundColor: '#FFD700', borderRadius: 5 },
  daysRow: { flexDirection: 'row', justifyContent: 'space-between' },
  dayDot: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.05)', borderWidth: 0, borderColor: 'rgba(255,255,255,0.1)',
    justifyContent: 'center', alignItems: 'center',
  },
  dayDotActive: { backgroundColor: 'rgba(255,215,0,0.2)', borderColor: '#FFD700' },
  dayText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#555' },
  dayTextActive: { color: '#FFD700' },
  perksTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#FFD700', marginBottom: 12 },
  perkCard: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: 'rgba(255,255,255,0.04)', borderRadius: 12, padding: 14, marginBottom: 8,
    borderWidth: 0, borderColor: 'rgba(255,255,255,0.08)',
  },
  perkLocked: { opacity: 0.5 },
  perkIcon: {
    width: 44, height: 44, borderRadius: 12,
    backgroundColor: 'rgba(255,255,255,0.05)', justifyContent: 'center', alignItems: 'center',
  },
  perkInfo: { flex: 1 },
  perkTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 8, color: '#FFF', marginBottom: 4 },
  perkDesc: { fontFamily: 'PressStart2P_400Regular', fontSize: 6, color: '#888' },
  howToSection: {
    backgroundColor: 'rgba(255,215,0,0.05)', borderRadius: 16, padding: 16, marginTop: 16,
    borderWidth: 0, borderColor: 'rgba(255,215,0,0.1)',
  },
  howToTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 9, color: '#FFD700', marginBottom: 16 },
  howToStep: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 12 },
  stepNum: {
    width: 28, height: 28, borderRadius: 14,
    backgroundColor: 'rgba(255,215,0,0.2)', justifyContent: 'center', alignItems: 'center',
  },
  stepNumText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10, color: '#FFD700' },
  stepText: { fontFamily: 'PressStart2P_400Regular', fontSize: 6, color: '#CCC', flex: 1, lineHeight: 12 },
});
