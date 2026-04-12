import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Dimensions, Animated, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../src/context/AuthContext';
import { Ionicons } from '@expo/vector-icons';

const { width } = Dimensions.get('window');

export default function WelcomeScreen() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;

  useEffect(() => {
    if (!loading && user) {
      router.replace('/home');
    }
  }, [user, loading]);

  useEffect(() => {
    // Pulse animation for logo
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.05, duration: 1200, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 1200, useNativeDriver: true }),
      ])
    ).start();

    // Fade-in content
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 800, useNativeDriver: true }),
      Animated.timing(slideAnim, { toValue: 0, duration: 800, useNativeDriver: true }),
    ]).start();
  }, []);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Ionicons name="code-slash" size={40} color="#00FF88" />
        <Text style={styles.loadingText}>LOADING...</Text>
      </View>
    );
  }

  return (
    <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          bounces={false}
        >
          {/* Logo Section */}
          <View style={styles.logoSection}>
            <Animated.View style={[styles.logoContainer, { transform: [{ scale: pulseAnim }] }]}>
              <Ionicons name="code-slash" size={56} color="#00FF88" />
            </Animated.View>
            <Text style={styles.title}>CODERO</Text>
            <Text style={styles.subtitle}>LEARN TO CODE</Text>
            <Text style={styles.tagline}>THE FUN WAY TO MASTER PROGRAMMING</Text>
          </View>

          {/* Features Grid */}
          <Animated.View style={[styles.featuresContainer, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
            <View style={styles.featureRow}>
              <View style={styles.featureCard}>
                <View style={[styles.featureIconBg, { backgroundColor: 'rgba(0, 255, 136, 0.12)' }]}>
                  <Ionicons name="globe" size={22} color="#00FF88" />
                </View>
                <Text style={styles.featureTitle}>20 LANGUAGES</Text>
                <Text style={styles.featureDesc}>PYTHON, JS, GO, RUST, ZIG & MORE</Text>
              </View>
              <View style={styles.featureCard}>
                <View style={[styles.featureIconBg, { backgroundColor: 'rgba(255, 215, 0, 0.12)' }]}>
                  <Ionicons name="trophy" size={22} color="#FFD700" />
                </View>
                <Text style={styles.featureTitle}>EARN XP</Text>
                <Text style={styles.featureDesc}>LEVEL UP & UNLOCK BADGES</Text>
              </View>
            </View>
            <View style={styles.featureRow}>
              <View style={styles.featureCard}>
                <View style={[styles.featureIconBg, { backgroundColor: 'rgba(255, 107, 107, 0.12)' }]}>
                  <Ionicons name="game-controller" size={22} color="#FF6B6B" />
                </View>
                <Text style={styles.featureTitle}>PLAY GAMES</Text>
                <Text style={styles.featureDesc}>BUG HUNTER, PUZZLES & MORE</Text>
              </View>
              <View style={styles.featureCard}>
                <View style={[styles.featureIconBg, { backgroundColor: 'rgba(0, 191, 255, 0.12)' }]}>
                  <Ionicons name="flame" size={22} color="#00BFFF" />
                </View>
                <Text style={styles.featureTitle}>STREAKS</Text>
                <Text style={styles.featureDesc}>DAILY GOALS & CHALLENGES</Text>
              </View>
            </View>
          </Animated.View>

          {/* Stats Highlight */}
          <View style={styles.statsRow}>
            <View style={styles.statBubble}>
              <Text style={styles.statNumber}>600+</Text>
              <Text style={styles.statLabel}>LESSONS</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statBubble}>
              <Text style={styles.statNumber}>3</Text>
              <Text style={styles.statLabel}>GAMES</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statBubble}>
              <Text style={styles.statNumber}>20+</Text>
              <Text style={styles.statLabel}>BADGES</Text>
            </View>
          </View>

          {/* Buttons */}
          <View style={styles.buttonContainer}>
            <TouchableOpacity
              style={styles.playButton}
              onPress={() => router.push('/register')}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#00FF88', '#00CC6A']}
                style={styles.playButtonGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Ionicons name="rocket" size={22} color="#0D0D0D" />
                <Text style={styles.playButtonText}>GET STARTED</Text>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.loginButton}
              onPress={() => router.push('/login')}
              activeOpacity={0.8}
            >
              <Ionicons name="log-in" size={18} color="#00FF88" />
              <Text style={styles.loginButtonText}>I HAVE AN ACCOUNT</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.footerText}>FREE TO START - NO CREDIT CARD NEEDED</Text>
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
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 24,
    justifyContent: 'space-between',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0D0D0D',
    gap: 16,
  },
  loadingText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 12,
    color: '#00FF88',
  },
  logoSection: {
    alignItems: 'center',
    paddingTop: 16,
    marginBottom: 24,
  },
  logoContainer: {
    width: 100,
    height: 100,
    borderRadius: 24,
    backgroundColor: 'rgba(0, 255, 136, 0.1)',
    borderWidth: 3,
    borderColor: '#00FF88',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  title: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 28,
    color: '#00FF88',
    textShadowColor: '#00FF88',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 20,
    marginBottom: 10,
  },
  subtitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 11,
    color: '#FFFFFF',
    marginBottom: 8,
  },
  tagline: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 7,
    color: '#888888',
    textAlign: 'center',
    lineHeight: 14,
  },
  featuresContainer: {
    gap: 10,
    marginBottom: 20,
  },
  featureRow: {
    flexDirection: 'row',
    gap: 10,
  },
  featureCard: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.04)',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    alignItems: 'center',
    gap: 8,
  },
  featureIconBg: {
    width: 44,
    height: 44,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  featureTitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#FFFFFF',
    textAlign: 'center',
  },
  featureDesc: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 5,
    color: '#888888',
    textAlign: 'center',
    lineHeight: 10,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 255, 136, 0.05)',
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderColor: 'rgba(0, 255, 136, 0.1)',
    marginBottom: 24,
  },
  statBubble: {
    flex: 1,
    alignItems: 'center',
    gap: 4,
  },
  statNumber: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 14,
    color: '#00FF88',
  },
  statLabel: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 6,
    color: '#888888',
  },
  statDivider: {
    width: 1,
    height: 28,
    backgroundColor: 'rgba(0, 255, 136, 0.2)',
  },
  buttonContainer: {
    gap: 12,
    marginBottom: 16,
  },
  playButton: {
    borderRadius: 16,
    overflow: 'hidden',
    elevation: 8,
    shadowColor: '#00FF88',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  playButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    gap: 12,
  },
  playButtonText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 13,
    color: '#0D0D0D',
  },
  loginButton: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: '#00FF88',
    borderRadius: 16,
    paddingVertical: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  loginButtonText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 9,
    color: '#00FF88',
  },
  footerText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 6,
    color: '#555555',
    textAlign: 'center',
  },
});
