import React, { useState, useRef, useEffect, useCallback } from 'react';
import Video, { VideoRef } from 'react-native-video';
import {
  Camera,
  useCameraDevice,
  useCameraPermission,
  useMicrophonePermission,
  useVideoOutput,
} from 'react-native-vision-camera';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Platform,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useTheme } from './ThemeContext';
import { Exercise, API_BASE_URL } from '../services/api';

const videoByCategory: { [key: string]: any } = {
  body: require('../assets/videos/sample_body.mp4'),
  hands: require('../assets/videos/sample_hands.mp4'),
  legs: require('../assets/videos/sample_legs.mp4'),
};

type SessionState = 'idle' | 'recording' | 'uploading' | 'completed';

interface AnalysisError { joint: string; message: string }
interface AnalysisResult {
  score: number;
  errors: AnalysisError[];
  frames_analyzed: number;
}

const scoreColor = (s: number) => s >= 80 ? '#4CAF50' : s >= 50 ? '#FF9800' : '#F44336';

const ExerciseSession = () => {
  const navigation = useNavigation();
  const route = useRoute();
  const { colors } = useTheme();
  const exercise = (route.params as any)?.exercise as Exercise;

  const [sessionState, setSessionState] = useState<SessionState>('idle');
  const [elapsedTime, setElapsedTime] = useState(0);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const referenceVideoRef = useRef<VideoRef>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const recorderRef = useRef<any>(null);

  // vision-camera hooks
  const device = useCameraDevice('front');
  const { hasPermission: hasCam, requestPermission: requestCam } = useCameraPermission();
  const { hasPermission: hasMic, requestPermission: requestMic } = useMicrophonePermission();
  const videoOutput = useVideoOutput({ enableAudio: true });

  useEffect(() => {
    if (!hasCam) requestCam();
    if (!hasMic) requestMic();
  }, []);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      recorderRef.current?.stopRecording?.().catch(() => {});
    };
  }, []);

  const getVideoSource = () => {
    const key = exercise?.category ?? 'body';
    return videoByCategory[key] ?? videoByCategory['body'];
  };

  const formatTime = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;

  const uploadAndAnalyze = useCallback(async (filePath: string) => {
    setSessionState('uploading');
    setErrorMessage(null);

    try {
      const uri = Platform.OS === 'android' && !filePath.startsWith('file://')
        ? `file://${filePath}`
        : filePath;

      const formData = new FormData();
      formData.append('video', { uri, type: 'video/mp4', name: 'exercise.mp4' } as any);

      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/exercises/${exercise.id}/analyze`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `Ошибка сервера: ${response.status}`);
      }

      setAnalysisResult(await response.json());
      setSessionState('completed');
    } catch (e: any) {
      setErrorMessage(e.message || 'Ошибка при отправке видео');
      setSessionState('idle');
    }
  }, [exercise]);

  const startSession = useCallback(async () => {
    setElapsedTime(0);
    setErrorMessage(null);

    // Запускаем эталонное видео
    referenceVideoRef.current?.seek(0);
    setSessionState('recording');

    // Таймер
    timerRef.current = setInterval(() => setElapsedTime(t => t + 1), 1000);

    // Запись видео пользователя
    try {
      const recorder = await videoOutput.createRecorder({});
      recorderRef.current = recorder;
      await recorder.startRecording(
        (fp: string) => {
          if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
          uploadAndAnalyze(fp);
        },
        (err: Error) => {
          setErrorMessage(`Ошибка записи: ${err.message}`);
          setSessionState('idle');
        },
      );
    } catch (e: any) {
      setErrorMessage(`Не удалось начать запись: ${e.message}`);
      setSessionState('idle');
      if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    }
  }, [videoOutput, uploadAndAnalyze]);

  const finishSession = useCallback(async () => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    try {
      await recorderRef.current?.stopRecording();
    } catch (_) {}
    recorderRef.current = null;
    // uploadAndAnalyze будет вызван через onRecordingFinished
  }, []);

  const reset = useCallback(() => {
    setSessionState('idle');
    setAnalysisResult(null);
    setErrorMessage(null);
    setElapsedTime(0);
  }, []);

  // Экран результатов
  if (sessionState === 'completed') {
    const r = analysisResult;
    return (
      <ScrollView contentContainerStyle={[styles.feedbackScreen, { backgroundColor: colors.background }]}>
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
          <Text style={[styles.backBtnText, { color: colors.text }]}>← Назад</Text>
        </TouchableOpacity>

        <Text style={[styles.feedbackTitle, { color: colors.text }]}>Результат анализа</Text>

        {r && (
          <>
            <View style={[styles.scoreCard, { borderColor: scoreColor(r.score) }]}>
              <Text style={[styles.scoreLabel, { color: colors.text }]}>Оценка</Text>
              <Text style={[styles.scoreValue, { color: scoreColor(r.score) }]}>{r.score}</Text>
              <Text style={[styles.scoreVerdict, { color: colors.text }]}>
                {r.score >= 80 ? '✓ Отличная техника!' : r.score >= 50 ? '⚠ Есть ошибки' : '✗ Нужна практика'}
              </Text>
              <Text style={[styles.framesNote, { color: colors.text }]}>
                Проанализировано {r.frames_analyzed} кадров
              </Text>
            </View>

            {r.errors.length > 0 ? (
              <View style={[styles.errorsCard, { borderColor: colors.primary }]}>
                <Text style={[styles.errorsTitle, { color: colors.text }]}>Замечания:</Text>
                {r.errors.map((e, i) => (
                  <Text key={i} style={[styles.errorItem, { color: colors.text }]}>• {e.joint}: {e.message}</Text>
                ))}
              </View>
            ) : (
              <View style={[styles.errorsCard, { borderColor: '#4CAF50' }]}>
                <Text style={[styles.errorItem, { color: '#4CAF50' }]}>Все суставы в норме — отличная техника!</Text>
              </View>
            )}
          </>
        )}

        <TouchableOpacity style={[styles.greenBtn]} onPress={reset}>
          <Text style={styles.btnText}>Попробовать снова</Text>
        </TouchableOpacity>
      </ScrollView>
    );
  }

  // Экран загрузки
  if (sessionState === 'uploading') {
    return (
      <View style={[styles.centered, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={[styles.uploadingText, { color: colors.text }]}>
          Загрузка, подождите пожалуйста, это займет несколько минут
        </Text>
      </View>
    );
  }

  const isRecording = sessionState === 'recording';
  const cameraActive = sessionState === 'idle' || sessionState === 'recording';

  return (
    <View style={styles.container}>
      {/* Область видео — делит пространство поровну */}
      <View style={styles.videoArea}>
        {/* Верхняя половина — эталонное видео */}
        <View style={styles.half}>
          <Video
            ref={referenceVideoRef}
            source={getVideoSource()}
            style={StyleSheet.absoluteFill}
            paused={!isRecording}
            resizeMode="cover"
            repeat={false}
            controls={false}
            muted={false}
            onEnd={isRecording ? finishSession : undefined}
          />
          <View style={styles.panelLabel}>
            <Text style={styles.panelLabelText}>Эталонное упражнение</Text>
          </View>
          <TouchableOpacity style={styles.backOverlayBtn} onPress={() => navigation.goBack()}>
            <Text style={styles.backOverlayText}>←</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.divider} />

        {/* Нижняя половина — камера пользователя */}
        <View style={styles.half}>
          {device && (hasCam && hasMic) ? (
            <Camera
              style={StyleSheet.absoluteFill}
              device={device}
              outputs={[videoOutput]}
              isActive={cameraActive}
              resizeMode="cover"
              mirrorMode="auto"
            />
          ) : (
            <View style={[StyleSheet.absoluteFill, styles.noCameraContainer]}>
              <Text style={styles.noCameraText}>
                {!hasCam || !hasMic
                  ? 'Разрешите доступ к камере и микрофону'
                  : 'Камера недоступна'}
              </Text>
            </View>
          )}
          <View style={styles.panelLabel}>
            <Text style={styles.panelLabelText}>Ваша камера</Text>
          </View>
          {isRecording && (
            <View style={styles.recIndicator}>
              <View style={styles.recDot} />
              <Text style={styles.recText}>REC {formatTime(elapsedTime)}</Text>
            </View>
          )}
        </View>
      </View>

      {/* Нижняя панель управления */}
      <View style={[styles.controls, { backgroundColor: colors.background }]}>
        {errorMessage && (
          <Text style={styles.errorText}>{errorMessage}</Text>
        )}

        {!isRecording ? (
          <TouchableOpacity style={styles.greenBtn} onPress={startSession} disabled={!hasCam || !hasMic}>
            <Text style={styles.btnText}>Начать упражнение</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={styles.greenBtn} onPress={finishSession}>
            <Text style={styles.btnText}>Завершить упражнение</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  videoArea: { flex: 1, flexDirection: 'column' },
  half: { height: '50%', overflow: 'hidden', backgroundColor: '#111' },
  divider: { height: 2, backgroundColor: 'rgba(255,255,255,0.15)' },

  panelLabel: {
    position: 'absolute', bottom: 8, left: 10,
    backgroundColor: 'rgba(0,0,0,0.55)', borderRadius: 8,
    paddingHorizontal: 10, paddingVertical: 4,
  },
  panelLabelText: { color: 'white', fontSize: 12, fontWeight: '500' },

  backOverlayBtn: {
    position: 'absolute', top: 12, left: 12,
    backgroundColor: 'rgba(0,0,0,0.45)', borderRadius: 20,
    paddingHorizontal: 12, paddingVertical: 6,
  },
  backOverlayText: { color: 'white', fontSize: 18 },

  recIndicator: {
    position: 'absolute', top: 10, right: 10,
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.6)', borderRadius: 20,
    paddingHorizontal: 10, paddingVertical: 5, gap: 6,
  },
  recDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#F44336' },
  recText: { color: 'white', fontSize: 13, fontWeight: '600' },

  noCameraContainer: { justifyContent: 'center', alignItems: 'center', backgroundColor: '#1a1a1a' },
  noCameraText: { color: 'rgba(255,255,255,0.5)', fontSize: 13, textAlign: 'center', paddingHorizontal: 24 },

  controls: { paddingHorizontal: 24, paddingTop: 12, paddingBottom: 16 },
  greenBtn: {
    backgroundColor: '#4CAF50', borderRadius: 12,
    paddingVertical: 16, alignItems: 'center',
  },
  btnText: { color: 'white', fontSize: 17, fontWeight: 'bold' },
  errorText: { color: '#F44336', fontSize: 13, textAlign: 'center', marginBottom: 10 },

  // Экран загрузки
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 16, paddingHorizontal: 32 },
  uploadingText: { fontSize: 17, fontWeight: '600', textAlign: 'center' },
  uploadingSubtext: { fontSize: 14, opacity: 0.6, textAlign: 'center' },

  // Экран результатов
  feedbackScreen: { flexGrow: 1, paddingHorizontal: 28, paddingTop: 56, paddingBottom: 48, gap: 20 },
  backBtn: { marginBottom: 4 },
  backBtnText: { fontSize: 15 },
  feedbackTitle: { fontSize: 24, fontWeight: 'bold', textAlign: 'center' },
  scoreCard: { borderWidth: 2, borderRadius: 16, padding: 24, alignItems: 'center', gap: 6 },
  scoreLabel: { fontSize: 13, opacity: 0.6 },
  scoreValue: { fontSize: 56, fontWeight: 'bold' },
  scoreVerdict: { fontSize: 15, fontWeight: '600' },
  framesNote: { fontSize: 11, opacity: 0.4, marginTop: 4 },
  errorsCard: { borderWidth: 1, borderRadius: 16, borderStyle: 'dashed', padding: 20, gap: 8 },
  errorsTitle: { fontSize: 15, fontWeight: '600', marginBottom: 4 },
  errorItem: { fontSize: 14, lineHeight: 22 },
});

export default ExerciseSession;
