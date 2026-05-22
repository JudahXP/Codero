import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Alert,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../src/services/api';

interface Friend {
  username: string;
  xp: number;
  level: number;
  streak: number;
}

export default function FriendsScreen() {
  const router = useRouter();
  const [friends, setFriends] = useState<Friend[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [addUsername, setAddUsername] = useState('');
  const [adding, setAdding] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [suggestions, setSuggestions] = useState<any[]>([]);


  useEffect(() => {
    fetchFriends();
  }, []);

  useEffect(() => {
    const query = addUsername.trim();
    if (!showAdd || query.length < 2) {
      setSuggestions([]);
      return;
    }
    const timeout = setTimeout(async () => {
      try {
        const response = await api.get(`/friends/suggest?q=${encodeURIComponent(query)}`);
        setSuggestions(response.data);
      } catch (error) {
        setSuggestions([]);
      }
    }, 180);
    return () => clearTimeout(timeout);
  }, [addUsername, showAdd]);


  const fetchFriends = async () => {
    try {
      const response = await api.get('/friends');
      setFriends(response.data);
    } catch (error) {
      console.error('Failed to fetch friends:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchFriends();
    setRefreshing(false);
  };

  const handleAddFriend = async () => {
    if (!addUsername.trim()) {
      Alert.alert('ERROR', 'Please enter a username');
      return;
    }

    setAdding(true);
    try {
      await api.post('/friends/add', { friend_username: addUsername.trim() });
      Alert.alert('SUCCESS', `Added ${addUsername} as friend!`);
      setAddUsername('');
      setSuggestions([]);
      setShowAdd(false);
      fetchFriends();
    } catch (error: any) {
      Alert.alert('ERROR', error.response?.data?.detail || 'Failed to add friend');
    } finally {
      setAdding(false);
    }
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
            <Text style={styles.title}>FRIENDS</Text>
            <Text style={styles.subtitle}>{friends.length} CODERS</Text>
          </View>
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => setShowAdd(!showAdd)}
          >
            <Ionicons name={showAdd ? 'close' : 'person-add'} size={20} color="#00FF88" />
          </TouchableOpacity>
        </View>

        {/* Add Friend */}
        {showAdd && (
          <View style={styles.addContainer}>
            <View style={styles.addInputContainer}>
              <Ionicons name="at" size={20} color="#00FF88" />
              <TextInput
                style={styles.addInput}
                value={addUsername}
                onChangeText={setAddUsername}
                placeholder="USERNAME"
                placeholderTextColor="#666"
                autoCapitalize="none"
              />
            </View>
            <TouchableOpacity
              style={styles.addSubmitButton}
              onPress={handleAddFriend}
              disabled={adding}
            >
              {adding ? (
                <ActivityIndicator size="small" color="#0D0D0D" />
              ) : (
                <Ionicons name="add" size={24} color="#0D0D0D" />
              )}
            </TouchableOpacity>
          </View>
        )}

        {/* Username Suggestions */}
        {showAdd && suggestions.length > 0 && (
          <View style={styles.suggestionsBox}>
            <Text style={styles.suggestionsLabel}>TAB COMPLETIONS</Text>
            {suggestions.map((suggestion) => (
              <TouchableOpacity
                key={suggestion.username}
                style={styles.suggestionPill}
                onPress={() => setAddUsername(suggestion.username)}
              >
                <Text style={styles.suggestionName}>{suggestion.username}</Text>
                <Text style={styles.suggestionMeta}>LV {suggestion.level}</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Friends List */}
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.scrollContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#00FF88" />
          }
        >
          {friends.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Ionicons name="people" size={60} color="#333" />
              <Text style={styles.emptyText}>NO FRIENDS YET</Text>
              <Text style={styles.emptySubtext}>ADD FRIENDS TO COMPETE!</Text>
            </View>
          ) : (
            friends.map((friend) => (
              <View key={friend.username} style={styles.friendCard}>
                <View style={styles.friendLeft}>
                  <View style={styles.friendAvatar}>
                    <Ionicons name="person" size={24} color="#00FF88" />
                  </View>
                  <View style={styles.friendInfo}>
                    <Text style={styles.friendName}>{friend.username.toUpperCase()}</Text>
                    <Text style={styles.friendLevel}>LEVEL {friend.level}</Text>
                  </View>
                </View>
                <View style={styles.friendRight}>
                  <View style={styles.friendStat}>
                    <Ionicons name="star" size={16} color="#FFD700" />
                    <Text style={styles.friendStatValue}>{friend.xp}</Text>
                  </View>
                  <View style={styles.friendStat}>
                    <Ionicons name="flame" size={16} color="#FF6B6B" />
                    <Text style={styles.friendStatValue}>{friend.streak}</Text>
                  </View>
                </View>
              </View>
            ))
          )}
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
    fontSize: 16,
    color: '#00FF88',
  },
  subtitle: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#888',
    marginTop: 4,
  },
  addButton: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: 'rgba(0, 255, 136, 0.1)',
    borderWidth: 1,
    borderColor: '#00FF88',
    justifyContent: 'center',
    alignItems: 'center',
  },
  addContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    marginBottom: 16,
  suggestionsBox: {
    marginHorizontal: 20,
    marginTop: -6,
    marginBottom: 16,
    padding: 12,
    borderRadius: 12,
    backgroundColor: 'rgba(0,0,0,0.35)',
    borderWidth: 1,
    borderColor: 'rgba(0,255,136,0.25)',
    gap: 8,
  },
  suggestionsLabel: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 7,
    color: '#00FF88',
  },
  suggestionPill: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    minHeight: 44,
    paddingHorizontal: 12,
    borderRadius: 10,
    backgroundColor: 'rgba(255,255,255,0.06)',
  },
  suggestionName: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 9,
    color: '#FFF',
  },
  suggestionMeta: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 7,
    color: '#888',
  },

    gap: 12,
  },
  addInputContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    paddingHorizontal: 16,
    height: 50,
    borderWidth: 1,
    borderColor: 'rgba(0, 255, 136, 0.3)',
  },
  addInput: {
    flex: 1,
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#FFF',
    marginLeft: 12,
  },
  addSubmitButton: {
    width: 50,
    height: 50,
    borderRadius: 12,
    backgroundColor: '#00FF88',
    justifyContent: 'center',
    alignItems: 'center',
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    gap: 12,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingTop: 60,
  },
  emptyText: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 12,
    color: '#555',
    marginTop: 16,
  },
  emptySubtext: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 8,
    color: '#444',
    marginTop: 8,
  },
  friendCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(0, 255, 136, 0.2)',
  },
  friendLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  friendAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(0, 255, 136, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  friendInfo: {
    flex: 1,
  },
  friendName: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 10,
    color: '#FFF',
  },
  friendLevel: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 7,
    color: '#888',
    marginTop: 4,
  },
  friendRight: {
    flexDirection: 'row',
    gap: 16,
  },
  friendStat: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  friendStatValue: {
    fontFamily: 'PressStart2P_400Regular',
    fontSize: 9,
    color: '#FFF',
  },
  bottomPadding: {
    height: 40,
  },
});
