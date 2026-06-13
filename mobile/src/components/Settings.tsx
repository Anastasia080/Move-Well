import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useNavigation } from '@react-navigation/native';
import BottomMenu from './BottomMenu';
import { useTheme } from './ThemeContext';

type RootStackParamList = {
  Profile: undefined;
  Main: undefined;
  Favorite: undefined;
  Settings: undefined;
  Login: undefined;
  About: { previousScreen?: string } | undefined;
};
type SettingsScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Settings'>;

const Settings = () => {
  const navigation = useNavigation<SettingsScreenNavigationProp>();
  const { theme, colors, toggleTheme } = useTheme();
  
  const handleLogin = () => {
    navigation.navigate('Login');
  };

  const handleThemeChange = (selectedTheme: 'light' | 'dark') => {
    toggleTheme(selectedTheme);
  };

  const handleAboutPress = () => {
    navigation.navigate('About', { previousScreen: 'Settings' });
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>

        <Text style={[styles.settingsTitle, { color: colors.text }]}>Настройки</Text>

        <ScrollView 
          style={styles.scrollView} 
          contentContainerStyle={styles.scrollContent} 
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
            <View style={styles.settingsLinks}>
              <Text style={[styles.settingsLinksText, { color: colors.text }]}>Уведомления</Text>
              <Text style={[styles.settingsLinksText, { color: colors.text }]}>Политика конфиденциальности</Text>
              <Text style={[styles.settingsLinksText, { color: colors.text }]}>Контакты</Text>
              <TouchableOpacity onPress={handleAboutPress}>
                <Text style={[styles.settingsLinksText, { color: colors.text }]}>О приложении</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.changeTheme}>
              <Text style={[styles.changeThemeTitle, { color: colors.text }]}>Тема</Text>
              <View style={styles.changeThemeButton}>
                <TouchableOpacity 
                  style={[
                    styles.lightThemeButton, 
                    theme === 'light' 
                      ? { backgroundColor: colors.buttonBg } 
                      : { borderColor: colors.buttonOutline }
                  ]}
                  onPress={() => handleThemeChange('light')}
                >
                  <Text style={[
                    theme === 'light' 
                      ? styles.lightThemeButtonTextActive 
                      : styles.lightThemeButtonTextInactive,
                    theme === 'light' 
                      ? { color: colors.buttonText } 
                      : { color: colors.buttonOutlineText }
                  ]}>
                    Светлая
                  </Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                  style={[
                    styles.darkThemeButton, 
                    theme === 'dark' 
                      ? { backgroundColor: colors.buttonBg } 
                      : { borderColor: colors.buttonOutline }
                  ]}
                  onPress={() => handleThemeChange('dark')}
                >
                  <Text style={[
                    theme === 'dark' 
                      ? styles.darkThemeButtonTextActive 
                      : styles.darkThemeButtonTextInactive,
                    theme === 'dark' 
                      ? { color: colors.buttonText } 
                      : { color: colors.buttonOutlineText }
                  ]}>
                    Темная
                  </Text>
                </TouchableOpacity>
              </View>
            </View>

            <View style={styles.settingsAccountButton}>
              <TouchableOpacity 
                style={[styles.exitButton, { backgroundColor: colors.buttonBg }]} 
                onPress={handleLogin}
              >
                <Text style={[styles.exitButtonText, { color: colors.buttonText }]}>
                  Выйти из аккаунта
                </Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={[styles.deleteButton, { borderColor: colors.buttonOutline }]}
              >
                <Text style={[styles.deleteButtonText, { color: colors.buttonOutlineText }]}>
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
  darkThemeButton: {
    borderWidth: 2,
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 20,
    alignItems: 'center',
    borderColor: 'transparent',
  },
  darkThemeButtonTextActive: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  darkThemeButtonTextInactive: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  lightThemeButton: {
    borderWidth: 2,
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 20,
    alignItems: 'center',
    borderColor: 'transparent',
  },
  lightThemeButtonTextActive: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  lightThemeButtonTextInactive: {
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
    borderWidth: 2,
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