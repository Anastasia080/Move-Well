import React, { useState, useEffect, useRef } from 'react';
import Video, { VideoRef } from 'react-native-video';
import {
  View,
  Text,
  StyleSheet,
  Image,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  GestureResponderEvent,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useNavigation, useRoute } from '@react-navigation/native';
import BottomMenu from './BottomMenu';
import { useTheme } from './ThemeContext';
import { apiService, Exercise } from '../services/api';

const videoByCategory: { [key: string]: any } = {
  body: require('../assets/videos/sample_body.mp4'),
  hands: require('../assets/videos/sample_hands.mp4'),
  legs: require('../assets/videos/sample_legs.mp4'),
};

type RootStackParamList = {
  Profile: undefined;
  Main: undefined;
  Favorite: undefined;
  Settings: undefined;
  ShowVideo: { video: Exercise };
  ExerciseSession: { exercise: Exercise };
};

type ShowVideoScreenNavigationProp = NativeStackNavigationProp<
  RootStackParamList,
  'ShowVideo'
>;


const ShowVideo = () => {
  const navigation = useNavigation<ShowVideoScreenNavigationProp>();
  const route = useRoute();
  const { colors } = useTheme();
  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [loading, setLoading] = useState(true);
  const [isFavorite, setIsFavorite] = useState(false);
  const [paused, setPaused] = useState(true);
  const [videoError, setVideoError] = useState(false);
  const [videoErrorMsg, setVideoErrorMsg] = useState('');
  const [videoLoading, setVideoLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [progressBarWidth, setProgressBarWidth] = useState(0);

  const videoRef = useRef<VideoRef>(null);

  const videoFromParams = (route.params as any)?.video as Exercise;

  useEffect(() => {
    if (videoFromParams) {
      setExercise(videoFromParams);
      setIsFavorite(videoFromParams.is_favorite === 1);
      setLoading(false);
    }
  }, []);

  const handleToggleFavorite = async () => {
    if (!exercise) return;

    try {
      if (isFavorite) {
        await apiService.removeFromFavorites(exercise.id);
        setIsFavorite(false);
      } else {
        await apiService.addToFavorites(exercise.id);
        setIsFavorite(true);
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
    }
  };

  const getVideoSource = () => {
    const key = exercise?.category ?? 'body';
    return videoByCategory[key] ?? videoByCategory['body'];
  };

  const handleVideoLoad = (data: { duration: number }) => {
    setDuration(data.duration);
    setVideoLoading(false);
    setVideoError(false);
  };

  const handleVideoError = (error: any) => {
    const msg = JSON.stringify(error);
    console.error('[VIDEO ERROR]', msg);
    setVideoErrorMsg(msg);
    setVideoError(true);
    setVideoLoading(false);
  };

  const handlePlayPause = () => {
    setPaused(!paused);
  };
  const handleProgress = (data: { currentTime: number }) => {
    setCurrentTime(data.currentTime);
  };

  const handleProgressBarLayout = (event: any) => {
    setProgressBarWidth(event.nativeEvent.layout.width);
  };

  const handleSeek = (event: GestureResponderEvent) => {
    if (duration === 0 || progressBarWidth === 0) return;
    const { locationX } = event.nativeEvent;
    const ratio = Math.max(0, Math.min(1, locationX / progressBarWidth));
    videoRef.current?.seek(ratio * duration);
    setCurrentTime(ratio * duration);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
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

  if (!exercise) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <Text style={{ color: colors.text }}>Видео не найдено</Text>
        <BottomMenu />
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <View style={styles.headermenu}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Image
            source={require('../assets/icons/left-arrow.png')}
            style={[styles.backIcon, { tintColor: colors.primary }]}
          />
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.heartButton}
          onPress={handleToggleFavorite}
        >
          <Image
            source={
              isFavorite
                ? require('../assets/icons/favorite.png')
                : require('../assets/icons/add-to-favorites.png')
            }
            style={[styles.heartIcon, { tintColor: colors.primary }]}
          />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* Видеоплеер */}
        <View style={styles.videoPlayer}>
          <Video
            ref={videoRef}
            source={getVideoSource()}
            style={styles.video}
            paused={paused}
            resizeMode="contain"
            onLoad={handleVideoLoad}
            onProgress={handleProgress}
            onError={handleVideoError}
            repeat={false}
            controls={false}
            ignoreSilentSwitch="ignore"
            playInBackground={false}
            playWhenInactive={false}
          />

          {/* Прозрачный оверлей для tap-to-play */}
          <TouchableOpacity
            style={styles.videoOverlay}
            onPress={handlePlayPause}
            activeOpacity={1}
          >
            {!videoLoading && !videoError && (
              <View style={styles.playIconContainer}>
                <Image
                  source={require('../assets/icons/play.png')}
                  style={[
                    styles.playIconWhite,
                    { opacity: paused ? 1 : 0.5 },
                  ]}
                />
              </View>
            )}
          </TouchableOpacity>

          {/* Индикатор загрузки */}
          {videoLoading && !videoError && (
            <View style={styles.loadingOverlay}>
              <ActivityIndicator size="large" color={colors.primary} />
              <Text style={styles.loadingText}>Загрузка видео...</Text>
            </View>
          )}

          {/* Ошибка загрузки */}
          {videoError && (
            <View style={styles.errorOverlay}>
              <Text style={styles.errorText}>Ошибка загрузки видео</Text>
              <Text style={styles.errorDetail} selectable>{videoErrorMsg}</Text>
              <TouchableOpacity
                style={styles.retryButton}
                onPress={() => {
                  setVideoError(false);
                  setVideoLoading(true);
                  setPaused(true);
                }}
              >
                <Text style={styles.retryText}>Повторить</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Прогресс-бар */}
        {!videoError && (
          <View style={styles.progressContainer}>
            <Text style={[styles.timeText, { color: colors.text }]}>
              {formatTime(currentTime)}
            </Text>
            <TouchableOpacity
              style={styles.progressBarOuter}
              onLayout={handleProgressBarLayout}
              onPress={handleSeek}
              activeOpacity={1}
            >
              <View
                style={[
                  styles.progressBarFill,
                  {
                    width:
                      duration > 0
                        ? `${(currentTime / duration) * 100}%`
                        : '0%',
                    backgroundColor: colors.primary,
                  },
                ]}
              />
            </TouchableOpacity>
            <Text style={[styles.timeText, { color: colors.text }]}>
              {formatTime(duration)}
            </Text>
          </View>
        )}

        {/* Кнопки управления */}
        <View style={styles.bottomButtons}>
          <TouchableOpacity
            style={[styles.playButton, { backgroundColor: colors.card || '#e0e0e0' }]}
            onPress={handlePlayPause}
          >
            <Text style={[styles.playButtonText, { color: colors.text }]}>
              {!paused && !videoLoading && !videoError ? 'Пауза' : 'Смотреть'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.startButton, { backgroundColor: colors.buttonBg || '#4CAF50' }]}
            onPress={() => navigation.navigate('ExerciseSession', { exercise })}
          >
            <Text style={[styles.startButtonText, { color: colors.buttonText || '#ffffff' }]}>
              Начать
            </Text>
          </TouchableOpacity>
        </View>

        <Text style={[styles.videoTitle, { color: colors.text }]}>
          {exercise.title}
        </Text>

        <Text style={[styles.videoDescription, { color: colors.text }]}>
          {exercise.description}
        </Text>

        <Text style={[styles.disclaimer, { color: colors.text }]}>
          Видео и информация несут рекомендательный характер и не являются
          лечением. Необходима консультация со специалистом.
        </Text>
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
  scrollView: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollContent: {
    paddingBottom: 100,
    paddingTop: 20,
  },
  headermenu: {
    display: 'flex',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 70,
    marginBottom: 20,
  },
  videoPlayer: {
    width: '100%',
    aspectRatio: 16 / 9,
    borderRadius: 12,
    marginBottom: 30,
    backgroundColor: '#000',
    position: 'relative',
    overflow: 'hidden',
  },
  video: {
    width: '100%',
    height: '100%',
  },
  videoDuration: {
    color: 'white',
    fontSize: 12,
  },
  videoThumbnail: {
    width: '100%',
    height: '100%',
    position: 'absolute',
  },
  playIconContainer: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: [{ translateX: -24 }, { translateY: -24 }],
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1,
  },
  playIcon: {
    width: 24,
    height: 24,
    marginLeft: 2,
  },
  videoInfoOverlay: {
    position: 'absolute',
    bottom: 8,
    right: 8,
    backgroundColor: 'rgba(0,0,0,0.7)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    zIndex: 1,
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 2,
  },
  loadingText: {
    color: 'white',
    marginTop: 10,
    fontSize: 14,
  },
  errorOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 2,
  },
  errorText: {
    color: 'white',
    fontSize: 16,
    marginBottom: 6,
    textAlign: 'center',
  },
  errorDetail: {
    color: '#ffaaaa',
    fontSize: 10,
    marginBottom: 10,
    textAlign: 'center',
    paddingHorizontal: 8,
  },
  retryButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: '#4CAF50',
    borderRadius: 8,
  },
  retryText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
  },
  videoTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 50,
  },
  videoDescription: {
    fontSize: 20,
    marginBottom: 50,
  },
  keyPointsContainer: {
    marginBottom: 20,
  },
  keyPointsTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 10,
  },
  keyPoint: {
    fontSize: 14,
    marginBottom: 5,
    lineHeight: 20,
  },
  disclaimer: {
    fontSize: 14,
    color: '#c4c2c2',
  },
  heartButton: {
    width: 34,
    height: 34,
    backgroundColor: 'transparent',
    justifyContent: 'center',
    alignItems: 'center',
  },
  heartIcon: {
    width: 34,
    height: 34,
  },
  backButton: {
    width: 34,
    height: 34,
    backgroundColor: 'transparent',
    justifyContent: 'center',
    alignItems: 'center',
  },
  backIcon: {
    width: 34,
    height: 34,
  },
  videoOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
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
  startButton: {
    flex: 1,
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 20,
    alignItems: 'center',
  },

  startButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    gap: 8,
  },
  progressBarOuter: {
    flex: 1,
    height: 4,
    backgroundColor: '#e0e0e0',
    borderRadius: 2,
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 2,
  },
  timeText: {
    fontSize: 12,
    minWidth: 36,
    textAlign: 'center',
  },
  bottomButtons: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  playButton: {
    flex: 1,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
  },
  playButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default ShowVideo;
