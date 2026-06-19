import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Pressable, Dimensions, Animated } from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../src/context/AuthContext';
import { Ionicons } from '@expo/vector-icons';

const { width } = Dimensions.get('window');

export default function WelcomeScreen() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!loading && user) {
      router.replace('/home');
    }
  }, [user, loading]);

  useEffect(() => {
    Animated.timing(fadeAnim, { toValue: 1, duration: 600, useNativeDriver: true }).start();
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
    <View style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <Animated.View style={[styles.content, { opacity: fadeAnim }]}>
          {/* Logo Section */}
          <View style={styles.logoSection}>
            <View style={styles.logoContainer}>
              <Ionicons name="code-slash" size={50} color="#00FF88" />
            </View>
            <Text style={styles.title}>CODERO</Text>
            <Text style={styles.subtitle}>LEARN TO CODE</Text>
            <Text style={styles.tagline}>THE FUN WAY TO MASTER PROGRAMMING</Text>
          </View>

          {/* Features */}
          <View style={styles.featuresContainer}>
            <View style={styles.featureRow}>
              <View style={styles.featureCard}>
                <Ionicons name="globe" size={24} color="#00FF88" />
                <Text style={styles.featureTitle}>20 LANGUAGES</Text>
              </View>
              <View style={styles.featureCard}>
                <Ionicons name="trophy" size={24} color="#FFD700" />
                <Text style={styles.featureTitle}>EARN XP</Text>
              </View>
            </View>
            <View style={styles.featureRow}>
              <View style={styles.featureCard}>
                <Ionicons name="game-controller" size={24} color="#FF6B6B" />
                <Text style={styles.featureTitle}>PLAY GAMES</Text>
              </View>
              <View style={styles.featureCard}>
                <Ionicons name="flame" size={24} color="#00BFFF" />
                <Text style={styles.featureTitle}>STREAKS</Text>
              </View>
            </View>
          </View>

          {/* Stats */}
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

          {/* Buttons - Using Pressable for better web touch handling */}
          <View style={styles.buttonContainer}>
            <Pressable
              style={({ pressed }) => [styles.playButton, pressed && styles.buttonPressed]}
              onPress={() => router.push('/register')}
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
            </Pressable>

            <Pressable
              style={({ pressed }) => [styles.loginButton, pressed && styles.loginPressed]}
              onPress={() => router.push('/login')}
            >
              <Ionicons name="log-in" size={18} color="#00FF88" />
              <Text style={styles.loginButtonText}>I HAVE AN ACCOUNT</Text>
            </Pressable>
          </View>

          <Text style={styles.footerText}>FREE TO START - NO CREDIT CARD NEEDED</Text>
        </Animated.View>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0D0D0D',
  },
  safeArea: {
    flex: 1,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 16,
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
  },
  logoContainer: {
    width: 90,
    height: 90,
    borderRadius: 22,
    backgroundColor: 'rgba(0, 255, 136, 0.1)',
    borderWidth: 0,
    borderColor: '#00FF88',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 26,
    color: '#00FF88',
    textShadowColor: '#00FF88',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 20,
    marginBottom: 8,
  },
  subtitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#FFFFFF',
    marginBottom: 6,
  },
  tagline: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 6,
    color: '#888888',
    textAlign: 'center',
    lineHeight: 12,
  },
  featuresContainer: {
    gap: 8,
  },
  featureRow: {
    flexDirection: 'row',
    gap: 8,
  },
  featureCard: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.04)',
    borderRadius: 12,
    paddingVertical: 12,
    borderWidth: 0,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    alignItems: 'center',
    gap: 6,
  },
  featureTitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 7,
    color: '#FFFFFF',
    textAlign: 'center',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 255, 136, 0.05)',
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderWidth: 0,
    borderColor: 'rgba(0, 255, 136, 0.1)',
  },
  statBubble: {
    flex: 1,
    alignItems: 'center',
    gap: 3,
  },
  statNumber: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 13,
    color: '#00FF88',
  },
  statLabel: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 5,
    color: '#888888',
  },
  statDivider: {
    width: 1,
    height: 24,
    backgroundColor: 'rgba(0, 255, 136, 0.2)',
  },
  buttonContainer: {
    gap: 12,
  },
  playButton: {
    borderRadius: 16,
    overflow: 'hidden',
  },
  buttonPressed: {
    opacity: 0.7,
    transform: [{ scale: 0.98 }],
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
    borderWidth: 0,
    borderColor: '#00FF88',
    borderRadius: 16,
    paddingVertical: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  loginPressed: {
    opacity: 0.7,
    backgroundColor: 'rgba(0, 255, 136, 0.05)',
  },
  loginButtonText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 9,
    color: '#00FF88',
  },
  footerText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 5,
    color: '#555555',
    textAlign: 'center',
  },
});
