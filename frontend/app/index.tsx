import React, { useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Dimensions, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../src/context/AuthContext';
import { Ionicons } from '@expo/vector-icons';

const { width, height } = Dimensions.get('window');

export default function WelcomeScreen() {
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && user) {
      router.replace('/home');
    }
  }, [user, loading]);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>LOADING...</Text>
      </View>
    );
  }

  return (
    <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.content}>
          {/* Logo Section */}
          <View style={styles.logoSection}>
            <View style={styles.logoContainer}>
              <Ionicons name="code-slash" size={60} color="#00FF88" />
            </View>
            <Text style={styles.title}>CODERO</Text>
            <Text style={styles.subtitle}>LEARN TO CODE</Text>
            <Text style={styles.tagline}>LEVEL UP YOUR SKILLS</Text>
          </View>

          {/* Features */}
          <View style={styles.featuresContainer}>
            <View style={styles.featureRow}>
              <View style={styles.featureBadge}>
                <Ionicons name="game-controller" size={20} color="#00FF88" />
              </View>
              <Text style={styles.featureText}>16 LANGUAGES</Text>
            </View>
            <View style={styles.featureRow}>
              <View style={styles.featureBadge}>
                <Ionicons name="trophy" size={20} color="#FFD700" />
              </View>
              <Text style={styles.featureText}>EARN XP & BADGES</Text>
            </View>
            <View style={styles.featureRow}>
              <View style={styles.featureBadge}>
                <Ionicons name="flame" size={20} color="#FF6B6B" />
              </View>
              <Text style={styles.featureText}>DAILY STREAKS</Text>
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
                <Ionicons name="play" size={24} color="#0D0D0D" />
                <Text style={styles.playButtonText}>START</Text>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.loginButton}
              onPress={() => router.push('/login')}
              activeOpacity={0.8}
            >
              <Text style={styles.loginButtonText}>ALREADY HAVE ACCOUNT</Text>
            </TouchableOpacity>
          </View>
        </View>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0D0D0D',
  },
  loadingText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 14,
    color: '#00FF88',
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    justifyContent: 'space-between',
    paddingVertical: 40,
  },
  logoSection: {
    alignItems: 'center',
    paddingTop: 40,
  },
  logoContainer: {
    width: 120,
    height: 120,
    borderRadius: 24,
    backgroundColor: 'rgba(0, 255, 136, 0.1)',
    borderWidth: 3,
    borderColor: '#00FF88',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  title: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 32,
    color: '#00FF88',
    textShadowColor: '#00FF88',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 20,
    marginBottom: 12,
  },
  subtitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 12,
    color: '#FFFFFF',
    marginBottom: 8,
  },
  tagline: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#888888',
  },
  featuresContainer: {
    gap: 16,
    paddingVertical: 20,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  featureBadge: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  featureText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#FFFFFF',
  },
  buttonContainer: {
    gap: 16,
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
    fontSize: 16,
    color: '#0D0D0D',
  },
  loginButton: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: '#00FF88',
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: 'center',
  },
  loginButtonText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#00FF88',
  },
});
