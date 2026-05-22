import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../src/context/AuthContext';

export default function RegisterScreen() {
  const router = useRouter();
  const { register } = useAuth();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleRegister = async () => {
    if (!username.trim() || !email.trim() || !password.trim()) {
      Alert.alert('ERROR', 'Please fill in all fields');
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert('ERROR', 'Passwords do not match');
      return;
    }

    if (password.length < 4) {
      Alert.alert('ERROR', 'Password must be at least 4 characters');
      return;
    }

    setLoading(true);
    try {
      await register(username.trim(), email.trim(), password);
      router.replace('/verify-email');
    } catch (error: any) {
      Alert.alert('ERROR', error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <LinearGradient colors={['#0D0D0D', '#1A1A2E', '#0D0D0D']} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardView}
        >
          <ScrollView contentContainerStyle={styles.scrollContent}>
            {/* Back Button */}
            <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
              <Ionicons name="arrow-back" size={24} color="#00FF88" />
            </TouchableOpacity>

            {/* Header */}
            <View style={styles.header}>
              <Ionicons name="person-add" size={48} color="#00FF88" />
              <Text style={styles.title}>REGISTER</Text>
              <Text style={styles.subtitle}>CREATE YOUR ACCOUNT</Text>
            </View>

            {/* Form */}
            <View style={styles.form}>
              <View style={styles.inputContainer}>
                <Ionicons name="person" size={20} color="#00FF88" style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder="USERNAME"
                  placeholderTextColor="#666666"
                  value={username}
                  onChangeText={setUsername}
                  autoCapitalize="none"
                />
              </View>

              <View style={styles.inputContainer}>
                <Ionicons name="mail" size={20} color="#00FF88" style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder="EMAIL"
                  placeholderTextColor="#666666"
                  value={email}
                  onChangeText={setEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
              </View>

              <View style={styles.inputContainer}>
                <Ionicons name="lock-closed" size={20} color="#00FF88" style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder="PASSWORD"
                  placeholderTextColor="#666666"
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry={!showPassword}
                />
                <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
                  <Ionicons name={showPassword ? 'eye-off' : 'eye'} size={20} color="#666666" />
                </TouchableOpacity>
              </View>

              <View style={styles.inputContainer}>
                <Ionicons name="shield-checkmark" size={20} color="#00FF88" style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder="CONFIRM PASSWORD"
                  placeholderTextColor="#666666"
                  value={confirmPassword}
                  onChangeText={setConfirmPassword}
                  secureTextEntry={!showPassword}
                />
              </View>

              <TouchableOpacity
                style={styles.registerButton}
                onPress={handleRegister}
                disabled={loading}
                activeOpacity={0.8}
              >
                <LinearGradient
                  colors={['#00FF88', '#00CC6A']}
                  style={styles.registerButtonGradient}
                >
                  {loading ? (
                    <ActivityIndicator color="#0D0D0D" />
                  ) : (
                    <>
                      <Ionicons name="rocket" size={20} color="#0D0D0D" />
                      <Text style={styles.registerButtonText}>START</Text>
                    </>
                  )}
                </LinearGradient>
              </TouchableOpacity>

              <TouchableOpacity onPress={() => router.push('/login')}>
                <Text style={styles.loginLink}>HAVE ACCOUNT? LOGIN</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
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
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: 24,
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
  header: {
    alignItems: 'center',
    marginTop: 24,
    marginBottom: 32,
  },
  title: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 20,
    color: '#00FF88',
    marginTop: 16,
  },
  subtitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#888888',
    marginTop: 8,
  },
  form: {
    gap: 16,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 2,
    borderColor: 'rgba(0, 255, 136, 0.3)',
    borderRadius: 12,
    paddingHorizontal: 16,
    height: 56,
  },
  inputIcon: {
    marginRight: 12,
  },
  input: {
    flex: 1,
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 9,
    color: '#FFFFFF',
  },
  registerButton: {
    borderRadius: 12,
    overflow: 'hidden',
    marginTop: 16,
  },
  registerButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    gap: 12,
  },
  registerButtonText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 14,
    color: '#0D0D0D',
  },
  loginLink: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#00FF88',
    textAlign: 'center',
    marginTop: 12,
  },
});
