import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useNavigation, CommonActions } from '@react-navigation/native';
import BottomMenu from './BottomMenu';
import { useTheme } from './ThemeContext';
import { apiService } from '../services/api';

type RootStackParamList = {
  Profile: undefined;
  Main: undefined;
  Favorite: undefined;
  Settings: undefined;
  Login: undefined;
  About: { previousScreen?: string } | undefined;
};

type SettingsScreenNavigationProp = NativeStackNavigationProp<
  RootStackParamList,
  'Settings'
>;

const Settings = () => {
  const navigation = useNavigation<SettingsScreenNavigationProp>();
  const { theme, colors, setThemeFromServer, getCurrentTheme } = useTheme();
  const [loading, setLoading] = useState(false);

  const handleLogout = () => {
    Alert.alert('Выход из аккаунта', 'Вы уверены, что хотите выйти?', [
      {
        text: 'Отмена',
        style: 'cancel',
      },
      {
        text: 'Выйти',
        style: 'destructive',
        onPress: async () => {
          setLoading(true);
          try {
            await apiService.logout();

            navigation.dispatch(
              CommonActions.reset({
                index: 0,
                routes: [{ name: 'Login' }],
              }),
            );
          } catch (error) {
            console.error('Logout error:', error);
            Alert.alert('Ошибка', 'Не удалось выйти из аккаунта');
          } finally {
            setLoading(false);
          }
        },
      },
    ]);
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      'Удаление аккаунта',
      'Вы уверены, что хотите удалить аккаунт? Это действие необратимо.',
      [
        {
          text: 'Отмена',
          style: 'cancel',
        },
        {
          text: 'Удалить',
          style: 'destructive',
          onPress: async () => {
            setLoading(true);
            try {
              await apiService.deleteAccount(true);
              await apiService.logout();
              navigation.dispatch(
                CommonActions.reset({
                  index: 0,
                  routes: [{ name: 'Login' }],
                }),
              );
              Alert.alert('Успех', 'Аккаунт успешно удален');
            } catch (error: any) {
              console.error('Delete account error:', error);
              Alert.alert(
                'Ошибка',
                error.message || 'Не удалось удалить аккаунт',
              );
            } finally {
              setLoading(false);
            }
          },
        },
      ],
    );
  };

  const handleThemeChange = async () => {
    setLoading(true);
    try {
      const currentTheme = getCurrentTheme();
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      console.log('🟢 Changing theme from', currentTheme, 'to', newTheme);
      const result = await apiService.updateProfile({ theme: newTheme });
      setThemeFromServer(newTheme);
      Alert.alert(
        'Успех',
        `Тема изменена на ${newTheme === 'dark' ? 'темную' : 'светлую'}`,
      );
    } catch (error: any) {
      console.error('🔴 Error saving theme:', error);
      Alert.alert('Ошибка', error.message || 'Не удалось сохранить тему');
    } finally {
      setLoading(false);
    }
  };

  const handleAboutPress = () => {
    navigation.navigate('About', { previousScreen: 'Settings' });
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <Text style={[styles.settingsTitle, { color: colors.text }]}>
        Настройки
      </Text>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.settingsLinks}>
          <TouchableOpacity>
            <Text style={[styles.settingsLinksText, { color: colors.text }]}>
              Уведомления
            </Text>
          </TouchableOpacity>
          <TouchableOpacity>
            <Text style={[styles.settingsLinksText, { color: colors.text }]}>
              Политика конфиденциальности
            </Text>
          </TouchableOpacity>
          <TouchableOpacity>
            <Text style={[styles.settingsLinksText, { color: colors.text }]}>
              Контакты
            </Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={handleAboutPress}>
            <Text style={[styles.settingsLinksText, { color: colors.text }]}>
              О приложении
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.changeTheme}>
          <Text style={[styles.changeThemeTitle, { color: colors.text }]}>
            Тема
          </Text>
          <View style={styles.changeThemeButton}>
            <TouchableOpacity
              style={[
                styles.themeButton,
                theme === 'light'
                  ? {
                      backgroundColor: colors.buttonBg,
                      borderColor: colors.primary,
                      borderWidth: 2,
                    }
                  : {
                      borderColor: colors.buttonOutline,
                      borderWidth: 2,
                      backgroundColor: 'transparent',
                    },
              ]}
              onPress={handleThemeChange}
            >
              <Text
                style={[
                  styles.themeButtonText,
                  theme === 'light'
                    ? { color: colors.buttonText }
                    : { color: colors.buttonOutlineText },
                ]}
              >
                Светлая
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.themeButton,
                theme === 'dark'
                  ? {
                      backgroundColor: colors.buttonBg,
                      borderColor: colors.primary,
                      borderWidth: 2,
                    }
                  : {
                      borderColor: colors.buttonOutline,
                      borderWidth: 2,
                      backgroundColor: 'transparent',
                    },
              ]}
              onPress={handleThemeChange}
            >
              <Text
                style={[
                  styles.themeButtonText,
                  theme === 'dark'
                    ? { color: colors.buttonText }
                    : { color: colors.buttonOutlineText },
                ]}
              >
                Темная
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.settingsAccountButton}>
          <TouchableOpacity
            style={[styles.exitButton, { backgroundColor: colors.buttonBg }]}
            onPress={handleLogout}
            disabled={loading}
          >
            <Text style={[styles.exitButtonText, { color: colors.buttonText }]}>
              {loading ? 'Выход...' : 'Выйти из аккаунта'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.deleteButton,
              { borderColor: colors.buttonOutline, borderWidth: 2 },
            ]}
            onPress={handleDeleteAccount}
            disabled={loading}
          >
            <Text
              style={[
                styles.deleteButtonText,
                { color: colors.buttonOutlineText },
              ]}
            >
              Удалить аккаунт
            </Text>
          </TouchableOpacity>
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
  settingsTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginTop: 80,
    marginBottom: 100,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 100,
  },
  settingsLinks: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    gap: 20,
    marginBottom: 50,
  },
  settingsLinksText: {
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'left',
  },
  changeTheme: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    marginBottom: 80,
  },
  changeThemeTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  changeThemeButton: {
    display: 'flex',
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    gap: 10,
  },
  themeButton: {
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 20,
    alignItems: 'center',
    flex: 1,
  },
  themeButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  settingsAccountButton: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-around',
    alignItems: 'center',
    gap: 15,
  },
  exitButton: {
    width: '100%',
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  exitButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  deleteButton: {
    width: '100%',
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  deleteButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default Settings;
