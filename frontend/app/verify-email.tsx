import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, Alert, ActivityIndicator, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../src/services/api';
import { useAuth } from '../src/context/AuthContext';
import { useAppSettings } from '../src/context/SettingsContext';

export default function VerifyEmailScreen() {
  const router = useRouter();
  const { user, refreshUser } = useAuth();
  const { colors, gradient, playSound } = useAppSettings();
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const email = user?.email || '';

  const resend = async () => {
    if (!email) return;
    try {
      setLoading(true);
      await api.post('/auth/send-verification-code', { email });
      playSound('notify');
      Alert.alert('CODE SENT', 'Check your email for a new Codero verification code.');
    } catch (error: any) {
      playSound('error');
      Alert.alert('ERROR', error.response?.data?.detail || 'Could not send code');
    } finally {
      setLoading(false);
    }
  };

  const verify = async () => {
    if (code.trim().length < 4) {
      Alert.alert('CODE NEEDED', 'Enter the code from your email.');
      return;
    }
    try {
      setLoading(true);
      await api.post('/auth/verify-email', { email, code: code.trim() });
      await refreshUser();
      playSound('success');
      router.replace('/home');
    } catch (error: any) {
      playSound('error');
      Alert.alert('ERROR', error.response?.data?.detail || 'Invalid verification code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <LinearGradient colors={gradient} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.wrap}>
          <View style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }]}> 
            <Ionicons name="mail-unread" size={54} color={colors.primary} />
            <Text style={[styles.title, { color: colors.primary }]}>VERIFY EMAIL</Text>
            <Text style={[styles.subtitle, { color: colors.textMuted }]}>Enter the code sent to {email || 'your Gmail'}.</Text>
            <TextInput
              style={[styles.input, { color: colors.text, backgroundColor: colors.card, borderColor: colors.border }]}
              value={code}
              onChangeText={setCode}
              placeholder="6-DIGIT CODE"
              placeholderTextColor={colors.textMuted}
              keyboardType="number-pad"
              maxLength={8}
            />
            <TouchableOpacity style={[styles.primaryButton, { backgroundColor: colors.primary }]} onPress={verify} disabled={loading}>
              {loading ? <ActivityIndicator color={colors.primaryText} /> : <Text style={[styles.primaryText, { color: colors.primaryText }]}>VERIFY + CONTINUE</Text>}
            </TouchableOpacity>
            <TouchableOpacity style={[styles.secondaryButton, { borderColor: colors.primary }]} onPress={resend} disabled={loading}>
              <Text style={[styles.secondaryText, { color: colors.primary }]}>RESEND CODE</Text>
            </TouchableOpacity>
            <Text style={[styles.subtitle, { color: colors.textMuted }]}>Verification is required before continuing. Check your email for the Codero code.</Text>
          </View>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  wrap: { flex: 1, justifyContent: 'center', padding: 24 },
  card: { borderWidth: 0, borderRadius: 22, padding: 24, alignItems: 'center', gap: 16 },
  title: { fontFamily: 'PressStart2P_400Regular', fontSize: 14, textAlign: 'center' },
  subtitle: { fontSize: 14, lineHeight: 20, textAlign: 'center' },
  input: { width: '100%', minHeight: 54, borderRadius: 14, borderWidth: 0, paddingHorizontal: 16, textAlign: 'center', fontSize: 18, fontWeight: '900', letterSpacing: 4 },
  primaryButton: { width: '100%', minHeight: 52, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  primaryText: { fontFamily: 'PressStart2P_400Regular', fontSize: 9 },
  secondaryButton: { width: '100%', minHeight: 48, borderRadius: 14, borderWidth: 0, alignItems: 'center', justifyContent: 'center' },
  secondaryText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8 },
  skipText: { fontSize: 13, fontWeight: '700' },
});
