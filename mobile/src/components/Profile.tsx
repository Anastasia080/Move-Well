import React, { useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import Slider from '@react-native-community/slider';
import { useTheme } from './ThemeContext';
import { apiService } from '../services/api';
import BottomMenu from './BottomMenu';

type RootStackParamList = {
  Main: undefined;
  Login: undefined;
  Profile: { isNewUser?: boolean } | undefined;
  About: { isNewUser?: boolean } | undefined;
};

type ProfileScreenNavigationProp = NativeStackNavigationProp<
  RootStackParamList,
  'Profile'
>;
type ProfileScreenRouteProp = RouteProp<RootStackParamList, 'Profile'>;

const MOBILITY_LIMITS_OPTIONS = [
  'Ограничение подвижности плеча',
  'Ограничение подвижности колена',
  'Ограничение подвижности тазобедренного сустава',
  'Ограничение подвижности позвоночника',
  'Ограничение подвижности локтя',
  'Ограничение подвижности запястья',
  'Общие ограничения',
];

const DIAGNOSIS_OPTIONS = [
  'Артрит',
  'Артроз',
  'Остеопороз',
  'Сколиоз',
  'Межпозвоночная грыжа',
  'Последствия травм',
  'Другое',
];

const Profile = () => {
  const navigation = useNavigation<ProfileScreenNavigationProp>();
  const route = useRoute<ProfileScreenRouteProp>();
  const { colors, setThemeFromServer } = useTheme();

  const [mobilityValue, setMobilityValue] = useState(1);
  const [selectedLimits, setSelectedLimits] = useState<string[]>([]);
  const [selectedDiagnosis, setSelectedDiagnosis] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [userEmail, setUserEmail] = useState<string>('');
  const [isEditing, setIsEditing] = useState(false);
  const [isNewUser, setIsNewUser] = useState(false);

  useEffect(() => {
    const params = route.params;
    if (params?.isNewUser) {
      setIsNewUser(true);
      setIsEditing(true);
    }
    loadUserData();
  }, []);

  const loadUserData = async () => {
    setLoading(true);
    try {
      const email = await AsyncStorage.getItem('user_email');
      if (email) {
        setUserEmail(email);
      }

      const profile = await apiService.getProfile();
      console.log('Loaded profile:', profile);
      setThemeFromServer(profile.theme || 'light');

      if (profile.mobility_limits && profile.mobility_limits.length > 0) {
        const limits = profile.mobility_limits.filter(limit =>
          MOBILITY_LIMITS_OPTIONS.includes(limit),
        );
        setSelectedLimits(limits);

        const level = profile.mobility_limits.find(
          limit =>
            limit === 'Низкий' || limit === 'Средний' || limit === 'Высокий',
        );
        if (level === 'Низкий') setMobilityValue(0);
        else if (level === 'Средний') setMobilityValue(1);
        else if (level === 'Высокий') setMobilityValue(2);
      }

      if (profile.diagnosis && profile.diagnosis.length > 0) {
        setSelectedDiagnosis(profile.diagnosis);
      }
    } catch (error: any) {
      console.error('Error loading user data:', error);
      if (error.message === 'No authentication token found') {
        navigation.navigate('Login');
      }
    } finally {
      setLoading(false);
    }
  };

  const getLevelText = (value: number) => {
    if (value === 0) return 'Низкий';
    if (value === 1) return 'Средний';
    return 'Высокий';
  };

  const toggleLimit = (limit: string) => {
    if (selectedLimits.includes(limit)) {
      setSelectedLimits(selectedLimits.filter(item => item !== limit));
    } else {
      setSelectedLimits([...selectedLimits, limit]);
    }
  };

  const toggleDiagnosis = (diagnosis: string) => {
    if (selectedDiagnosis.includes(diagnosis)) {
      setSelectedDiagnosis(
        selectedDiagnosis.filter(item => item !== diagnosis),
      );
    } else {
      setSelectedDiagnosis([...selectedDiagnosis, diagnosis]);
    }
  };

  const handleSave = async () => {
    setSaving(true);

    try {
      const mobilityLevel = getLevelText(mobilityValue);
      const mobilityLimits = [...selectedLimits];

      if (!mobilityLimits.includes(mobilityLevel)) {
        mobilityLimits.push(mobilityLevel);
      }

      await apiService.updateProfile({
        diagnosis: selectedDiagnosis,
        mobility_limits: mobilityLimits,
      });

      Alert.alert('Успех', 'Профиль успешно сохранен', [
        {
          text: 'OK',
          onPress: () => {
            setIsEditing(false);
            if (isNewUser) {
              navigation.navigate('Main');
            }
          },
        },
      ]);
    } catch (error: any) {
      console.error('Save error:', error);
      Alert.alert('Ошибка', error.message || 'Не удалось сохранить профиль');
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleCancel = () => {
    if (isNewUser) {
      Alert.alert(
        'Внимание',
        'Вы не сохранили профиль. Ваши данные будут потеряны. Продолжить?',
        [
          { text: 'Остаться', style: 'cancel' },
          {
            text: 'Выйти',
            style: 'destructive',
            onPress: () => navigation.navigate('Main'),
          },
        ],
      );
    } else {
      loadUserData();
      setIsEditing(false);
    }
  };

  const renderDiagnosisSection = () => {
    if (!isEditing && selectedDiagnosis.length === 0) return null;

    return (
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>
          Диагнозы
        </Text>
        {isEditing ? (
          <View style={styles.optionsContainer}>
            {DIAGNOSIS_OPTIONS.map((diagnosis, index) => (
              <TouchableOpacity
                key={index}
                style={[
                  styles.optionChip,
                  {
                    borderColor: colors.primary,
                    backgroundColor: selectedDiagnosis.includes(diagnosis)
                      ? colors.primary
                      : 'transparent',
                  },
                ]}
                onPress={() => toggleDiagnosis(diagnosis)}
              >
                <Text
                  style={[
                    styles.optionText,
                    {
                      color: selectedDiagnosis.includes(diagnosis)
                        ? '#ffffff'
                        : colors.text,
                    },
                  ]}
                >
                  {diagnosis}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        ) : (
          <View style={styles.optionsContainer}>
            {selectedDiagnosis.map((diagnosis, index) => (
              <View
                key={index}
                style={[
                  styles.selectedChip,
                  { backgroundColor: colors.primary + '20' },
                ]}
              >
                <Text style={[styles.selectedText, { color: colors.text }]}>
                  {diagnosis}
                </Text>
              </View>
            ))}
          </View>
        )}
      </View>
    );
  };

  const renderLimitsSection = () => {
    return (
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>
          Тип ограничения подвижности
        </Text>
        {isEditing ? (
          <View style={styles.optionsContainer}>
            {MOBILITY_LIMITS_OPTIONS.map((limit, index) => (
              <TouchableOpacity
                key={index}
                style={[
                  styles.optionChip,
                  {
                    borderColor: colors.primary,
                    backgroundColor: selectedLimits.includes(limit)
                      ? colors.primary
                      : 'transparent',
                  },
                ]}
                onPress={() => toggleLimit(limit)}
              >
                <Text
                  style={[
                    styles.optionText,
                    {
                      color: selectedLimits.includes(limit)
                        ? '#ffffff'
                        : colors.text,
                    },
                  ]}
                >
                  {limit}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        ) : (
          <View style={styles.optionsContainer}>
            {selectedLimits.length > 0 ? (
              selectedLimits.map((limit, index) => (
                <View
                  key={index}
                  style={[
                    styles.selectedChip,
                    { backgroundColor: colors.primary + '20' },
                  ]}
                >
                  <Text style={[styles.selectedText, { color: colors.text }]}>
                    {limit}
                  </Text>
                </View>
              ))
            ) : (
              <Text style={[styles.emptyText, { color: colors.text + '80' }]}>
                Не указано
              </Text>
            )}
          </View>
        )}
      </View>
    );
  };

  const renderMobilitySection = () => {
    return (
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>
          Уровень подвижности
        </Text>
        {isEditing ? (
          <View style={styles.sliderContainer}>
            <Slider
              value={mobilityValue}
              onValueChange={setMobilityValue}
              minimumValue={0}
              maximumValue={2}
              step={1}
              style={styles.slider}
              minimumTrackTintColor={colors.primary}
              maximumTrackTintColor="#e0e0e0"
              thumbTintColor={colors.primary}
            />
            <View style={styles.labelsContainer}>
              <Text style={[styles.label, { color: colors.text }]}>Низкий</Text>
              <Text style={[styles.label, { color: colors.text }]}>
                Средний
              </Text>
              <Text style={[styles.label, { color: colors.text }]}>
                Высокий
              </Text>
            </View>
            <Text style={[styles.currentLevel, { color: colors.primary }]}>
              Текущий уровень: {getLevelText(mobilityValue)}
            </Text>
          </View>
        ) : (
          <Text style={[styles.valueText, { color: colors.text }]}>
            {getLevelText(mobilityValue)}
          </Text>
        )}
      </View>
    );
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
      <Text style={[styles.profileTitle, { color: colors.text }]}>
        {isNewUser && !isEditing ? 'Мой профиль' : 'Профиль'}
      </Text>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        <View
          style={[
            styles.emailCard,
            {
              borderColor: colors.primary,
              backgroundColor: colors.primary + '10',
            },
          ]}
        >
          <Text style={[styles.emailLabel, { color: colors.text }]}>Email</Text>
          <Text style={[styles.emailValue, { color: colors.text }]}>
            {userEmail || 'Загрузка...'}
          </Text>
        </View>

        <View style={[styles.profileInfo, { borderColor: colors.primary }]}>
          {renderMobilitySection()}
          {renderLimitsSection()}
          {renderDiagnosisSection()}
        </View>

        <View style={styles.buttonContainer}>
          {!isEditing ? (
            <TouchableOpacity
              style={[styles.editButton, { backgroundColor: colors.primary }]}
              onPress={handleEdit}
            >
              <Text style={[styles.buttonText, { color: '#ffffff' }]}>
                Редактировать
              </Text>
            </TouchableOpacity>
          ) : (
            <>
              <TouchableOpacity
                style={[styles.cancelButton, { borderColor: colors.primary }]}
                onPress={handleCancel}
              >
                <Text
                  style={[styles.cancelButtonText, { color: colors.primary }]}
                >
                  Отмена
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.saveButton,
                  {
                    backgroundColor: colors.primary,
                    opacity: saving ? 0.6 : 1,
                  },
                ]}
                onPress={handleSave}
                disabled={saving}
              >
                {saving ? (
                  <ActivityIndicator color="#ffffff" />
                ) : (
                  <Text style={[styles.buttonText, { color: '#ffffff' }]}>
                    Сохранить
                  </Text>
                )}
              </TouchableOpacity>
            </>
          )}
        </View>
        <View style={{ height: 100 }} />
      </ScrollView>

      <BottomMenu />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 20,
  },
  profileTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginTop: 80,
    marginBottom: 30,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emailCard: {
    borderWidth: 2,
    borderRadius: 12,
    paddingHorizontal: 20,
    paddingVertical: 15,
    marginBottom: 20,
  },
  emailLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 5,
    opacity: 0.7,
  },
  emailValue: {
    fontSize: 18,
    fontWeight: '500',
  },
  profileInfo: {
    borderWidth: 2,
    borderRadius: 12,
    paddingHorizontal: 20,
    paddingVertical: 20,
    gap: 25,
  },
  section: {
    gap: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  optionsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  optionChip: {
    borderWidth: 1,
    borderRadius: 20,
    paddingVertical: 8,
    paddingHorizontal: 16,
    marginRight: 8,
    marginBottom: 8,
  },
  optionText: {
    fontSize: 14,
    fontWeight: '500',
  },
  selectedChip: {
    borderRadius: 20,
    paddingVertical: 8,
    paddingHorizontal: 16,
    marginRight: 8,
    marginBottom: 8,
  },
  selectedText: {
    fontSize: 14,
    fontWeight: '500',
  },
  emptyText: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  sliderContainer: {
    paddingHorizontal: 10,
  },
  slider: {
    width: '100%',
    height: 40,
  },
  labelsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 10,
    paddingHorizontal: 5,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
  },
  currentLevel: {
    textAlign: 'center',
    fontSize: 16,
    fontWeight: '600',
    marginTop: 15,
  },
  valueText: {
    fontSize: 16,
    fontWeight: '500',
    textAlign: 'center',
    paddingVertical: 10,
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 30,
    gap: 15,
  },
  editButton: {
    flex: 1,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
  },
  saveButton: {
    flex: 1,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
  },
  cancelButton: {
    flex: 1,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    borderWidth: 2,
  },
  buttonText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  cancelButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default Profile;
