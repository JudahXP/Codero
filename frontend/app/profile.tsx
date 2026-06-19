import React, { useMemo, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../src/services/api';
import { useAuth } from '../src/context/AuthContext';
import { useAppSettings } from '../src/context/SettingsContext';
import { safeBack } from '../src/utils/navigation';

export default function ProfileScreen() {
  const router = useRouter();
  const { user, logout, refreshUser } = useAuth();
  const { colors, gradient, fontScale, playSound } = useAppSettings();
  const [displayName, setDisplayName] = useState(user?.profile?.display_name || user?.username || '');
  const [bio, setBio] = useState(user?.profile?.bio || '');
  const displayBadges = useMemo(() => user?.profile?.display_badges?.slice(0, 3) || user?.badges?.slice(0, 3) || [], [user]);

  const getXPForNextLevel = () => (user?.level || 1) * 100;
  const getCurrentLevelXP = () => Math.max(0, (user?.xp || 0) - ((user?.level || 1) - 1) * 100);

  const saveProfile = async () => {
    try {
      playSound('tap');
      await api.put('/profile', { display_name: displayName.trim() || user?.username, bio: bio.trim() });
      if ((user?.badges || []).length > 0) {
        await api.put('/profile/display-badges', { badge_ids: (user?.badges || []).slice(0, 3) });
      }
      await refreshUser();
      playSound('success');
      Alert.alert('SAVED', 'Profile customization saved.');
    } catch (error: any) {
      playSound('error');
      Alert.alert('ERROR', error.response?.data?.detail || 'Could not save profile');
    }
  };

  const handleLogout = () => {
    playSound('tap');
    Alert.alert('LOGOUT', 'Are you sure you want to logout?', [
      { text: 'CANCEL', style: 'cancel' },
      {
        text: 'LOGOUT',
        style: 'destructive',
        onPress: async () => {
          await logout();
          router.replace('/');
        },
      },
    ]);
  };

  return (
    <LinearGradient colors={gradient} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.header}>
          <TouchableOpacity style={[styles.backButton, { borderColor: colors.primary, backgroundColor: colors.surface }]} onPress={() => safeBack(router)}>
            <Ionicons name="arrow-back" size={24} color={colors.primary} />
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: colors.primary, fontSize: 14 * fontScale }]}>PROFILE</Text>
          <View style={{ width: 44 }} />
        </View>

        <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent}>
          <View style={[styles.avatarSection, { backgroundColor: colors.surface, borderColor: colors.border }]}> 
            <View style={[styles.avatarContainer, { borderColor: user?.profile?.avatar_color || colors.primary, backgroundColor: colors.surfaceStrong }]}> 
              <Ionicons name="person" size={48} color={colors.primary} />
            </View>
            <Text style={[styles.username, { color: colors.text, fontSize: 16 * fontScale }]}>{(user?.profile?.display_name || user?.username || 'CODER').toUpperCase()}</Text>
            {user?.is_admin && (
              <View style={[styles.adminTag, { backgroundColor: colors.warning }]}>
                <Ionicons name="shield-checkmark" size={14} color="#0D0D0D" />
                <Text style={styles.adminTagText}>ADMIN</Text>
              </View>
            )}
            <Text style={[styles.email, { color: colors.textMuted }]}>{user?.email}</Text>
            {!!user?.profile?.bio && <Text style={[styles.bioText, { color: colors.textMuted }]}>{user.profile.bio}</Text>}
            <View style={styles.displayBadgesRow}>
              {[0, 1, 2].map((slot) => (
                <View key={slot} style={[styles.displayBadgeSlot, { borderColor: colors.warning, backgroundColor: colors.surfaceStrong }]}> 
                  {displayBadges[slot] ? (
                    <>
                      <Ionicons name="medal" size={18} color={colors.warning} />
                      <Text style={[styles.displayBadgeText, { color: colors.warning }]} numberOfLines={2}>{displayBadges[slot].replace(/_/g, ' ').toUpperCase()}</Text>
                    </>
                  ) : (
                    <Text style={[styles.emptyBadgeText, { color: colors.textMuted }]}>EMPTY SLOT</Text>
                  )}
                </View>
              ))}
            </View>
          </View>

          <View style={[styles.levelContainer, { backgroundColor: colors.surface, borderColor: colors.border }]}> 
            <View style={styles.levelHeader}>
              <View style={styles.levelBadge}>
                <Ionicons name="trophy" size={18} color={colors.warning} />
                <Text style={[styles.levelText, { color: colors.warning }]}>LEVEL {user?.level || 1}</Text>
              </View>
              <Text style={[styles.xpText, { color: colors.textMuted }]}>{getCurrentLevelXP()}/{getXPForNextLevel()} XP</Text>
            </View>
            <View style={[styles.levelBar, { backgroundColor: colors.border }]}> 
              <View style={[styles.levelProgress, { backgroundColor: colors.warning, width: `${Math.min((getCurrentLevelXP() / getXPForNextLevel()) * 100, 100)}%` }]} />
            </View>
          </View>

          <View style={[styles.customizeCard, { backgroundColor: colors.surface, borderColor: colors.border }]}> 
            <Text style={[styles.customizeTitle, { color: colors.primary }]}>CUSTOMIZE PROFILE</Text>
            <TextInput
              style={[styles.profileInput, { color: colors.text, borderColor: colors.border, backgroundColor: colors.card }]}
              value={displayName}
              onChangeText={setDisplayName}
              placeholder="Display name"
              placeholderTextColor={colors.textMuted}
              maxLength={32}
            />
            <TextInput
              style={[styles.profileInput, styles.bioInput, { color: colors.text, borderColor: colors.border, backgroundColor: colors.card }]}
              value={bio}
              onChangeText={setBio}
              placeholder="Short bio"
              placeholderTextColor={colors.textMuted}
              maxLength={160}
              multiline
            />
            <TouchableOpacity style={[styles.saveProfileButton, { backgroundColor: colors.primary }]} onPress={saveProfile}>
              <Ionicons name="save" size={18} color={colors.primaryText} />
              <Text style={[styles.saveProfileText, { color: colors.primaryText }]}>SAVE PROFILE</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.statsGrid}>
            {[{ icon: 'star', value: user?.xp || 0, label: 'TOTAL XP', color: colors.warning }, { icon: 'flame', value: user?.streak || 0, label: 'DAY STREAK', color: colors.danger }, { icon: 'heart', value: user?.hearts || 5, label: 'HEARTS', color: colors.danger }, { icon: 'diamond', value: user?.gems || 0, label: 'GEMS', color: colors.info }].map((stat) => (
              <View key={stat.label} style={[styles.statCard, { backgroundColor: colors.surface, borderColor: colors.border }]}> 
                <Ionicons name={stat.icon as any} size={28} color={stat.color} />
                <Text style={[styles.statValue, { color: colors.text }]}>{stat.value}</Text>
                <Text style={[styles.statLabel, { color: colors.textMuted }]}>{stat.label}</Text>
              </View>
            ))}
          </View>

          <View style={styles.menuSection}>
            {[{ route: '/settings', icon: 'settings', label: 'SETTINGS', color: colors.info }, { route: '/badges', icon: 'medal', label: 'VIEW BADGES', color: colors.danger }, { route: '/friends', icon: 'people', label: 'FRIENDS', color: colors.primary }, { route: '/leaderboard', icon: 'podium', label: 'LEADERBOARD', color: colors.warning }].map((item) => (
              <TouchableOpacity key={item.label} style={[styles.menuItem, { backgroundColor: colors.surface, borderColor: colors.border }]} onPress={() => { playSound('tap'); router.push(item.route as any); }}>
                <View style={styles.menuLeft}>
                  <View style={[styles.menuIcon, { backgroundColor: colors.card }]}> 
                    <Ionicons name={item.icon as any} size={22} color={item.color} />
                  </View>
                  <Text style={[styles.menuText, { color: colors.text }]}>{item.label}</Text>
                </View>
                <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity style={[styles.logoutButton, { borderColor: colors.danger, backgroundColor: colors.surface }]} onPress={handleLogout}>
            <Ionicons name="log-out" size={20} color={colors.danger} />
            <Text style={[styles.logoutText, { color: colors.danger }]}>LOGOUT</Text>
          </TouchableOpacity>
          <View style={styles.bottomPadding} />
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 20 },
  backButton: { width: 44, height: 44, borderRadius: 12, borderWidth: 0, justifyContent: 'center', alignItems: 'center' },
  headerTitle: { fontFamily: 'PressStart2P_400Regular' },
  scroll: { flex: 1 },
  scrollContent: { paddingHorizontal: 20, gap: 18 },
  avatarSection: { alignItems: 'center', borderRadius: 16, padding: 18, borderWidth: 1 },
  avatarContainer: { width: 100, height: 100, borderRadius: 50, borderWidth: 0, justifyContent: 'center', alignItems: 'center', marginBottom: 16 },
  username: { fontFamily: 'PressStart2P_400Regular', marginBottom: 8, textAlign: 'center' },
  email: { fontFamily: 'PressStart2P_400Regular', fontSize: 7, textAlign: 'center' },
  adminTag: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999, marginBottom: 8 },
  adminTagText: { fontFamily: 'PressStart2P_400Regular', fontSize: 7, color: '#0D0D0D' },

  bioText: { fontSize: 13, lineHeight: 19, textAlign: 'center', marginTop: 10 },
  displayBadgesRow: { flexDirection: 'row', gap: 8, marginTop: 16, width: '100%' },
  displayBadgeSlot: { flex: 1, minHeight: 64, borderRadius: 12, borderWidth: 0, alignItems: 'center', justifyContent: 'center', padding: 8, gap: 6 },
  displayBadgeText: { fontSize: 10, fontWeight: '700', textAlign: 'center', lineHeight: 13 },
  emptyBadgeText: { fontSize: 10, fontWeight: '700', textAlign: 'center' },
  levelContainer: { borderRadius: 12, padding: 16, borderWidth: 1 },
  levelHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  levelBadge: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  levelText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10 },
  xpText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8 },
  levelBar: { height: 10, borderRadius: 5, overflow: 'hidden' },
  levelProgress: { height: '100%', borderRadius: 5 },
  customizeCard: { borderRadius: 12, padding: 16, borderWidth: 0, gap: 12 },
  customizeTitle: { fontFamily: 'PressStart2P_400Regular', fontSize: 9 },
  profileInput: { fontSize: 15, minHeight: 48, borderRadius: 10, borderWidth: 0, paddingHorizontal: 12 },
  bioInput: { minHeight: 84, paddingTop: 12, textAlignVertical: 'top' },
  saveProfileButton: { minHeight: 48, borderRadius: 10, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  saveProfileText: { fontFamily: 'PressStart2P_400Regular', fontSize: 8 },
  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  statCard: { width: '47%', borderRadius: 12, padding: 16, alignItems: 'center', borderWidth: 1 },
  statValue: { fontFamily: 'PressStart2P_400Regular', fontSize: 18, marginVertical: 8 },
  statLabel: { fontFamily: 'PressStart2P_400Regular', fontSize: 7 },
  menuSection: { gap: 10 },
  menuItem: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', borderRadius: 12, padding: 14, borderWidth: 0, minHeight: 56 },
  menuLeft: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  menuIcon: { width: 40, height: 40, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  menuText: { fontFamily: 'PressStart2P_400Regular', fontSize: 9 },
  logoutButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, borderRadius: 12, padding: 16, borderWidth: 0, minHeight: 52 },
  logoutText: { fontFamily: 'PressStart2P_400Regular', fontSize: 10 },
  bottomPadding: { height: 40 },
});
