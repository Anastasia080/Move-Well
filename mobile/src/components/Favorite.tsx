import React, { useState, useEffect, useCallback  } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Image,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import BottomMenu from './BottomMenu';
import { useTheme } from './ThemeContext';
import SearchBox from './SearchBox';
import { apiService, Exercise } from '../services/api';

type RootStackParamList = {
  Profile: undefined;
  Main: undefined;
  Favorite: undefined;
  Settings: undefined;
  ShowVideo: { video: Exercise };
};

type FavoriteScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Favorite'>;
const thumbnailByCategory: { [key: string]: any } = {
  body: require('../assets/sample_body.jpg'),
  hands: require('../assets/sample_hands.jpg'),
  legs: require('../assets/sample_legs.jpg'),
};

const Favorite = () => {
  const navigation = useNavigation<FavoriteScreenNavigationProp>();
  const [search, setSearch] = useState('');
  const [favorites, setFavorites] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const { colors } = useTheme();

   const loadFavorites = async () => {
    try {
      const data = await apiService.getFavorites();
      setFavorites(data);
    } catch (error) {
      console.error('Error loading favorites:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFavorites();
  }, []);
  useFocusEffect(
    useCallback(() => {
      loadFavorites();
    }, [])
  );

  const onRefresh = async () => {
    setRefreshing(true);
    await loadFavorites();
    setRefreshing(false);
  };

  const handleRemoveFavorite = async (exercise: Exercise) => {
    try {
      await apiService.removeFromFavorites(exercise.id);
      setFavorites(prev => prev.filter(ex => ex.id !== exercise.id));
    } catch (error) {
      console.error('Error removing favorite:', error);
    }
  };

  const handleVideoPress = (video: Exercise) => {
    navigation.navigate('ShowVideo', { video });
  };

  const filteredFavorites = favorites.filter(video =>
    video.title.toLowerCase().includes(search.toLowerCase()) ||
    (video.description && video.description.toLowerCase().includes(search.toLowerCase()))
  );

  if (loading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }


  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
        <SearchBox 
        value={search}
        onChangeText={setSearch}
        onSearch={() => {}}
        onClear={() => setSearch('')}
        placeholder="Поиск в избранном"
       />
        
      <ScrollView 
        style={styles.scrollView} 
        contentContainerStyle={styles.scrollContent} 
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[colors.primary]} />
        }
      >
        <View style={styles.section}>
          <Text style={[styles.favoriteTitleText, { color: colors.text }]}>
            Избранные видео {favorites.length > 0 ? `(${favorites.length})` : ''}
          </Text>

          {favorites.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Image 
                source={require('../assets/icons/favorite.png')} 
                style={[styles.emptyIcon, { tintColor: colors.primary }]}
              />
              <Text style={[styles.emptyText, { color: colors.text }]}>
                Нет избранных видео
              </Text>
              <Text style={[styles.emptySubtext, { color: colors.text }]}>
                Добавляйте видео, нажимая на сердечко
              </Text>
            </View>
          ) : filteredFavorites.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Text style={[styles.emptyText, { color: colors.text }]}>
                По запросу "{search}" ничего не найдено
              </Text>
            </View>
          ) : (
            <View style={styles.videosGrid}>
              {filteredFavorites.map((video) => (
                <TouchableOpacity 
                  key={video.id} 
                  style={styles.videoCard}
                  onPress={() => handleVideoPress(video)}
                  activeOpacity={0.7}
                >
                  <View style={[styles.videoPlaceholder, { backgroundColor: colors.card }]}>
                    <Image
                      source={thumbnailByCategory[video.category] ?? thumbnailByCategory.body}
                      style={styles.videoThumbnail}
                      resizeMode="cover"
                    />
                    <View style={styles.playIconContainer}>
                      <Image 
                        source={require('../assets/icons/play.png')}
                        style={[styles.playIcon, { tintColor: 'white' }]}
                      />
                    </View>
                    <TouchableOpacity 
                      style={styles.heartButton}
                      onPress={() => handleRemoveFavorite(video)}
                    >
                      <Image 
                        source={require('../assets/icons/favorite.png')} 
                        style={[styles.heartIcon, { tintColor: colors.primary }]}
                      />
                    </TouchableOpacity>
                  </View>
                  <Text style={[styles.videoTitle, { color: colors.text }]} numberOfLines={1}>
                    {video.title}
                  </Text>
                  <Text style={[styles.videoDescription, { color: colors.text }]} numberOfLines={2}>
                    {video.description}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </View>
      </ScrollView>

      <BottomMenu />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 24,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 100,
    paddingTop: 20,
  },
  section: {
    display: 'flex',
    flexDirection: 'column',
  },
  favoriteSectionTitle: {
    display:'flex',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  favoriteTitleText: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  videosGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  videoCard: {
    width: '48%',
    marginBottom: 20,
  },
  videoPlaceholder: {
    width: '100%',
    aspectRatio: 16/9,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
    position: 'relative',
    overflow: 'hidden',
  },
  videoThumbnail: {
    width: '100%',
    height: '100%',
    position: 'absolute',
  },
  videoPlaceholderText: {
    fontSize: 14,
  },
  videoTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  videoDescription: {
    fontSize: 14,
  },
  heartButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 32,
    height: 32,
    backgroundColor: 'transparent',
    justifyContent: 'center',
    alignItems: 'center',
  },
  heartIcon: {
    width: 24,
    height: 24,
  },
  playIconContainer: {
    position: 'absolute',
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1,
  },
  playIcon: {
    width: 24,
    height: 24,
    marginLeft: 2,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyIcon: {
    width: 60,
    height: 60,
    marginBottom: 20,
    opacity: 0.5,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
    textAlign: 'center',
  },
  emptySubtext: {
    fontSize: 14,
    textAlign: 'center',
    opacity: 0.7,
  },
});

export default Favorite;