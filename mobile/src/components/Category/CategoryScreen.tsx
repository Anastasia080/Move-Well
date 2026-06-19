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
import {
  useNavigation,
  useRoute,
  useFocusEffect,
} from '@react-navigation/native';
import BottomMenu from '../BottomMenu';
import { useTheme } from '../ThemeContext';
import SearchBox from '../SearchBox';
import { apiService, Exercise } from '../../services/api';

const thumbnailByCategory: { [key: string]: any } = {
  body: require('../../assets/sample_body.jpg'),
  hands: require('../../assets/sample_hands.jpg'),
  legs: require('../../assets/sample_legs.jpg'),
};

type RootStackParamList = {
  ShowVideo: { video: Exercise };
};

type CategoryScreenNavigationProp = NativeStackNavigationProp<
  RootStackParamList,
  'ShowVideo'
>;

const CategoryScreen = () => {
  const navigation = useNavigation<CategoryScreenNavigationProp>();
  const route = useRoute();
  const { colors } = useTheme();
  const [search, setSearch] = useState('');
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const category = (route.params as any)?.category || '';

  const categoryTitle = getCategoryTitle(category);

  function getCategoryTitle(cat: string): string {
    switch (cat) {
      case 'legs':
        return 'Ноги';
      case 'hands':
        return 'Руки';
      case 'body':
        return 'Корпус';
      default:
        return 'Все видео';
    }
  }

  const loadExercises = async () => {
    try {
      const data = await apiService.getExercises(
        category || undefined,
        search || undefined,
      );
      setExercises(data);
    } catch (error) {
      console.error('Error loading exercises:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExercises();
  }, [category, search]);
  useFocusEffect(
    useCallback(() => {
      loadExercises();
    }, [category, search]),
  );
  const onRefresh = async () => {
    setRefreshing(true);
    await loadExercises();
    setRefreshing(false);
  };

  const handleToggleFavorite = async (exercise: Exercise) => {
    try {
      if (exercise.is_favorite === 1) {
        await apiService.removeFromFavorites(exercise.id);
      } else {
        await apiService.addToFavorites(exercise.id);
      }
      setExercises(prev =>
        prev.map(ex =>
          ex.id === exercise.id
            ? { ...ex, is_favorite: ex.is_favorite === 1 ? 0 : 1 }
            : ex,
        ),
      );
    } catch (error) {
      console.error('Error toggling favorite:', error);
    }
  };

  const handleVideoPress = (video: Exercise) => {
    navigation.navigate('ShowVideo', { video });
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
        onChangeText={setSearch}
        onSearch={() => {}}
        onClear={() => setSearch('')}
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
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>
            {categoryTitle}
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
              {exercises.map(exercise => (
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
                      source={thumbnailByCategory[exercise.category] ?? thumbnailByCategory.body}
                      style={styles.videoThumbnail}
                      resizeMode="cover"
                    />
                    <View style={styles.playIconContainer}>
                      <Image
                        source={require('../../assets/icons/play.png')}
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
                            ? require('../../assets/icons/favorite.png')
                            : require('../../assets/icons/add-to-favorites.png')
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
  scrollContent: {
    paddingBottom: 100,
    paddingTop: 20,
  },
  section: {
    flex: 1,
  },
  sectionTitle: {
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
    aspectRatio: 16 / 9,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
    position: 'relative',
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
  noResultsContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  noResultsText: {
    fontSize: 16,
    textAlign: 'center',
  },
  videoThumbnail: {
    width: '100%',
    height: '100%',
    position: 'absolute',
    borderRadius: 12,
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
  playIconWhite: {
    width: 24,
    height: 24,
    marginLeft: 2,
    tintColor: 'white',
  },
});

export default CategoryScreen;
