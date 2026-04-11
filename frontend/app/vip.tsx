import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
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

interface VIPInfo {
  price: number;
  currency: string;
  period: string;
  perks: Perk[];
}

export default function VIPScreen() {
  const router = useRouter();
  const { user, refreshUser } = useAuth();
  const [vipInfo, setVipInfo] = useState<VIPInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [subscribing, setSubscribing] = useState(false);

  useEffect(() => {
    fetchVIPInfo();
  }, []);

  const fetchVIPInfo = async () => {
    try {
      const response = await api.get('/vip/info');
      setVipInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch VIP info:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async () => {
    Alert.alert(
      'SUBSCRIBE TO VIP',
      `Unlock all VIP perks for $${vipInfo?.price}/${vipInfo?.period}?`,
      [
        { text: 'CANCEL', style: 'cancel' },
        {
          text: 'SUBSCRIBE',
          onPress: async () => {
            setSubscribing(true);
            try {
              const response = await api.post('/vip/subscribe', { payment_method: 'card' });
              Alert.alert('SUCCESS!', response.data.message);
              await refreshUser();
            } catch (error: any) {
              Alert.alert('ERROR', error.response?.data?.detail || 'Subscription failed');
            } finally {
              setSubscribing(false);
            }
          },
        },
      ]
    );
  };

  const isVIP = user?.is_vip || user?.vip_until;

  if (loading) {
    return (
      <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
        <SafeAreaView style={styles.centered}>
          <ActivityIndicator size="large" color="#FFD700" />
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
            <Ionicons name="arrow-back" size={24} color="#FFD700" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>VIP MEMBERSHIP</Text>
          <View style={{ width: 44 }} />
        </View>

        <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent}>
          {/* VIP Badge */}
          <View style={styles.vipBadge}>
            <LinearGradient
              colors={['#FFD700', '#FFA500']}
              style={styles.vipBadgeGradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <Ionicons name="star" size={48} color="#0D0D0D" />
            </LinearGradient>
            <Text style={styles.vipTitle}>CODERO VIP</Text>
            <Text style={styles.vipPrice}>
              ${vipInfo?.price}/{vipInfo?.period?.toUpperCase()}
            </Text>
          </View>

          {isVIP && (
            <View style={styles.activeCard}>
              <Ionicons name="checkmark-circle" size={24} color="#00FF88" />
              <Text style={styles.activeText}>VIP ACTIVE</Text>
              <Text style={styles.activeUntil}>
                Until: {new Date(user?.vip_until || '').toLocaleDateString()}
              </Text>
            </View>
          )}

          {/* Perks List */}
          <Text style={styles.perksTitle}>VIP PERKS</Text>
          <View style={styles.perksList}>
            {vipInfo?.perks.map((perk, index) => (
              <View key={index} style={styles.perkCard}>
                <View style={styles.perkIcon}>
                  <Ionicons name={perk.icon as any} size={24} color="#FFD700" />
                </View>
                <View style={styles.perkInfo}>
                  <Text style={styles.perkTitle}>{perk.title}</Text>
                  <Text style={styles.perkDesc}>{perk.description}</Text>
                </View>
              </View>
            ))}
          </View>

          {/* Comparison */}
          <View style={styles.comparisonSection}>
            <Text style={styles.comparisonTitle}>FREE VS VIP</Text>
            <View style={styles.comparisonTable}>
              <View style={styles.comparisonRow}>
                <Text style={styles.comparisonLabel}>HEARTS</Text>
                <Text style={styles.comparisonFree}>5</Text>
                <Text style={styles.comparisonVip}>10</Text>
              </View>
              <View style={styles.comparisonRow}>
                <Text style={styles.comparisonLabel}>XP MULTIPLIER</Text>
                <Text style={styles.comparisonFree}>1x</Text>
                <Text style={styles.comparisonVip}>1.5x</Text>
              </View>
              <View style={styles.comparisonRow}>
                <Text style={styles.comparisonLabel}>HINTS/LESSON</Text>
                <Text style={styles.comparisonFree}>1</Text>
                <Text style={styles.comparisonVip}>5</Text>
              </View>
              <View style={styles.comparisonRow}>
                <Text style={styles.comparisonLabel}>STREAK FREEZE</Text>
                <Text style={styles.comparisonFree}>0/WEEK</Text>
                <Text style={styles.comparisonVip}>2/WEEK</Text>
              </View>
              <View style={styles.comparisonRow}>
                <Text style={styles.comparisonLabel}>ADS</Text>
                <Text style={styles.comparisonFree}>YES</Text>
                <Text style={styles.comparisonVip}>NO</Text>
              </View>
            </View>
          </View>

          {/* Subscribe Button */}
          {!isVIP && (
            <TouchableOpacity
              style={styles.subscribeButton}
              onPress={handleSubscribe}
              disabled={subscribing}
            >
              <LinearGradient
                colors={['#FFD700', '#FFA500']}
                style={styles.subscribeGradient}
              >
                {subscribing ? (
                  <ActivityIndicator color="#0D0D0D" />
                ) : (
                  <>
                    <Ionicons name="star" size={20} color="#0D0D0D" />
                    <Text style={styles.subscribeText}>SUBSCRIBE NOW</Text>
                  </>
                )}
              </LinearGradient>
            </TouchableOpacity>
          )}

          {isVIP && (
            <TouchableOpacity
              style={styles.extendButton}
              onPress={handleSubscribe}
              disabled={subscribing}
            >
              <Text style={styles.extendText}>EXTEND MEMBERSHIP</Text>
            </TouchableOpacity>
          )}

          <View style={styles.bottomPadding} />
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
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
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    borderWidth: 1,
    borderColor: '#FFD700',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 12,
    color: '#FFD700',
  },
  scroll: { flex: 1 },
  scrollContent: { paddingHorizontal: 20 },
  vipBadge: {
    alignItems: 'center',
    marginVertical: 24,
  },
  vipBadgeGradient: {
    width: 100,
    height: 100,
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  vipTitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 20,
    color: '#FFD700',
    marginBottom: 8,
  },
  vipPrice: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 14,
    color: '#FFF',
  },
  activeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    backgroundColor: 'rgba(0, 255, 136, 0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#00FF88',
  },
  activeText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 12,
    color: '#00FF88',
  },
  activeUntil: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#888',
  },
  perksTitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 12,
    color: '#FFD700',
    marginBottom: 16,
  },
  perksList: { gap: 12, marginBottom: 24 },
  perkCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 215, 0, 0.05)',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.2)',
  },
  perkIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  perkInfo: { flex: 1 },
  perkTitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 9,
    color: '#FFD700',
    marginBottom: 4,
  },
  perkDesc: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 7,
    color: '#AAA',
  },
  comparisonSection: { marginBottom: 24 },
  comparisonTitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#FFF',
    marginBottom: 12,
  },
  comparisonTable: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    overflow: 'hidden',
  },
  comparisonRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  comparisonLabel: {
    flex: 1,
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 7,
    color: '#AAA',
  },
  comparisonFree: {
    width: 60,
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#888',
    textAlign: 'center',
  },
  comparisonVip: {
    width: 60,
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#FFD700',
    textAlign: 'center',
  },
  subscribeButton: {
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 16,
  },
  subscribeGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    gap: 12,
  },
  subscribeText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 12,
    color: '#0D0D0D',
  },
  extendButton: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: '#FFD700',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
  },
  extendText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#FFD700',
  },
  bottomPadding: { height: 40 },
});
