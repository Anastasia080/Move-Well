import React, { useState, useEffect, useCallback } from 'react';
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
import Category from './Category/Category';
import { useTheme } from './ThemeContext';
import SearchBox from './SearchBox';
import { apiService, Exercise } from '../services/api';

const thumbnailByCategory: { [key: string]: any } = {
  body: require('../assets/sample_body.jpg'),
  hands: require('../assets/sample_hands.jpg'),
  legs: require('../assets/sample_legs.jpg'),
};

type RootStackParamList = {
  Profile: undefined;
  Main: undefined;
  Favorite: undefined;
  Settings: undefined;
  ShowVideo: { video: Exercise };
};

type MainScreenNavigationProp = NativeStackNavigationProp<
  RootStackParamList,
  'Main'
>;

const Main = () => {
  const navigation = useNavigation<MainScreenNavigationProp>();
  const { colors } = useTheme();
  const [search, setSearch] = useState('');
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [recommended, setRecommended] = useState<Exercise[]>([]);

  const loadExercises = useCallback(async () => {
    try {
      const data = await apiService.getExercises(search || undefined);
      setExercises(data);
    } catch (error) {
      console.error('Error loading exercises:', error);
    } finally {
      setLoading(false);
    }
  }, [search]);

  const loadRecommended = useCallback(async () => {
    try {
      const data = await apiService.getRecommended();
      setRecommended(data);
    } catch (error) {
      console.error('Error loading recommendations:', error);
    }
  }, []);

  useEffect(() => {
    loadExercises();
  }, [loadExercises]);

  useFocusEffect(
    useCallback(() => {
      loadExercises();
      loadRecommended();
    }, [loadExercises, loadRecommended]),
  );

  const onRefresh = async () => {
    setRefreshing(true);
    await loadExercises();
    setRefreshing(false);
  };

  const handleToggleFavorite = async (exercise: Exercise) => {
    try {
      const updater = (prev: Exercise[]) =>
        prev.map(ex =>
          ex.id === exercise.id
            ? { ...ex, is_favorite: exercise.is_favorite === 1 ? 0 : 1 }
            : ex,
        );

      if (exercise.is_favorite === 1) {
        await apiService.removeFromFavorites(exercise.id);
      } else {
        await apiService.addToFavorites(exercise.id);
      }

      setExercises(updater);
      setRecommended(updater);
    } catch (error) {
      console.error('Error toggling favorite:', error);
    }
  };

  const handleVideoPress = (video: Exercise) => {
    navigation.navigate('ShowVideo', { video });
  };

  const handleChangeText = (text: string) => {
    setSearch(text);
  };

  const handleClear = () => {
    setSearch('');
  };

  const getVideoThumbnail = (exercise: Exercise) => {
    return thumbnailByCategory[exercise.category] ?? thumbnailByCategory.body;
  };

  if (loading) {
    return (
      <View
        style={[
          styles.loadingContainer,
          { backgroundColor: colors.background },
        ]}
      >
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <SearchBox
        value={search}
        onChangeText={handleChangeText}
        onSearch={() => {}}
        onClear={handleClear}
      />

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={[colors.primary]}
          />
        }
      >
        <Category />

        {recommended.length > 0 && !search && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>
              Рекомендовано для вас
            </Text>
            <View style={styles.videosGrid}>
              {recommended.map((exercise) => (
                <TouchableOpacity
                  key={`rec-${exercise.id}`}
                  style={styles.videoCard}
                  onPress={() => handleVideoPress(exercise)}
                  activeOpacity={0.7}
                >
                  <View
                    style={[
                      styles.videoPlaceholder,
                      { backgroundColor: colors.card },
                    ]}
                  >
                    <Image
                      source={getVideoThumbnail(exercise)}
                      style={styles.videoThumbnail}
                      resizeMode="cover"
                    />
                    <View style={styles.playIconContainer}>
                      <Image
                        source={require('../assets/icons/play.png')}
                        style={styles.playIconWhite}
                      />
                    </View>
                    <TouchableOpacity
                      style={styles.heartButton}
                      onPress={e => {
                        e.stopPropagation();
                        handleToggleFavorite(exercise);
                      }}
                    >
                      <Image
                        source={
                          exercise.is_favorite === 1
                            ? require('../assets/icons/favorite.png')
                            : require('../assets/icons/add-to-favorites.png')
                        }
                        style={[
                          styles.heartIcon,
                          { tintColor: colors.primary },
                        ]}
                      />
                    </TouchableOpacity>
                  </View>
                  <Text
                    style={[styles.videoTitle, { color: colors.text }]}
                    numberOfLines={1}
                  >
                    {exercise.title}
                  </Text>
                  <Text
                    style={[styles.videoDescription, { color: colors.text }]}
                    numberOfLines={2}
                  >
                    {exercise.description}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}

        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>
            Все упражнения
          </Text>

          {exercises.length === 0 ? (
            <View style={styles.noResultsContainer}>
              <Text style={[styles.noResultsText, { color: colors.text }]}>
                {search
                  ? `По запросу "${search}" ничего не найдено`
                  : 'Нет доступных упражнений'}
              </Text>
            </View>
          ) : (
            <View style={styles.videosGrid}>
              {exercises.map((exercise) => (
                <TouchableOpacity
                  key={exercise.id}
                  style={styles.videoCard}
                  onPress={() => handleVideoPress(exercise)}
                  activeOpacity={0.7}
                >
                  <View
                    style={[
                      styles.videoPlaceholder,
                      { backgroundColor: colors.card },
                    ]}
                  >
                    <Image
                      source={getVideoThumbnail(exercise)}
                      style={styles.videoThumbnail}
                      resizeMode="cover"
                    />
                    <View style={styles.playIconContainer}>
                      <Image
                        source={require('../assets/icons/play.png')}
                        style={styles.playIconWhite}
                      />
                    </View>
                    <TouchableOpacity
                      style={styles.heartButton}
                      onPress={e => {
                        e.stopPropagation();
                        handleToggleFavorite(exercise);
                      }}
                    >
                      <Image
                        source={
                          exercise.is_favorite === 1
                            ? require('../assets/icons/favorite.png')
                            : require('../assets/icons/add-to-favorites.png')
                        }
                        style={[
                          styles.heartIcon,
                          { tintColor: colors.primary },
                        ]}
                      />
                    </TouchableOpacity>
                  </View>
                  <Text
                    style={[styles.videoTitle, { color: colors.text }]}
                    numberOfLines={1}
                  >
                    {exercise.title}
                  </Text>
                  <Text
                    style={[styles.videoDescription, { color: colors.text }]}
                    numberOfLines={2}
                  >
                    {exercise.description}
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
  section: {
    display: 'flex',
    flexDirection: 'column',
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  scrollContent: {
    paddingBottom: 100,
    paddingTop: 20,
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
    aspectRatio: 16 / 9,
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
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 2,
  },
  heartIcon: {
    width: 24,
    height: 24,
  },
  searchResultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  searchResultsTitle: {
    fontSize: 22,
    fontWeight: 'bold',
  },
  resultsCount: {
    fontSize: 16,
    fontWeight: '600',
  },
  noResultsContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  noResultsText: {
    fontSize: 16,
    textAlign: 'center',
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
  playIconWhite: {
    width: 24,
    height: 24,
    marginLeft: 2,
    tintColor: 'white',
  },
});

export default Main;
