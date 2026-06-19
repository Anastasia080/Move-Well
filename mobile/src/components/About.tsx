import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Image,
  ActivityIndicator,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { useTheme } from './ThemeContext';
import {apiService} from '../services/api';

type RootStackParamList = {
  Profile: { isNewUser?: boolean } | undefined;
  Settings: undefined;
  About: { isNewUser?: boolean; previousScreen?: string } | undefined;
};
type AboutScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'About'>;
type AboutScreenRouteProp = RouteProp<RootStackParamList, 'About'>;
const About = () => {
  const navigation = useNavigation<AboutScreenNavigationProp>();
  const route = useRoute<AboutScreenRouteProp>();
  const { colors, setThemeFromServer } = useTheme();
  const [loading, setLoading] = useState(true);
  const previousRoute = route.params?.previousScreen || '';
  const isFromSettings = previousRoute === 'Settings';
  const isNewUser = route.params?.isNewUser || false;

  useEffect(() => {
    const loadTheme = async () => {
      try {
        const profile = await apiService.getProfile();
        setThemeFromServer(profile.theme || 'light');
      } catch (error) {
        console.error('Error loading theme:', error);
      } finally {
        setLoading(false);
      }
    };
    loadTheme();
  }, []);

  const handleButtonPress = () => {
    if (isFromSettings) {
      navigation.goBack();
    } else {
      navigation.navigate('Profile', { isNewUser: isNewUser });
    }
  };

  if (loading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <View style={styles.header}>
        <Image 
          source={require('../assets/logo.png')} 
          style={styles.logo} 
        />
        <Text style={[styles.appName,{ color: colors.text }]}>Move Well</Text>
      </View>

        <Text style={[styles.aboutTitle, { color: colors.text }]}>Добро пожаловать в Move Well!</Text>
        <Text style={[styles.aboutText, { color: colors.text }]}>Move Well - мобильное 
            приложение для реабилитации и физической терапии. 
            Оно является персональным помощником для людей с ограниченными 
            возможностями, 
            предоставляя персонализированные рекомендации для эффективного 
            восстановления.</Text>

        <TouchableOpacity 
        style={[styles.forwardButton, { backgroundColor: colors.buttonBg }]} 
        onPress={handleButtonPress}
        >
          <Text style={[styles.forwardButtonText, { color: colors.buttonText }]}>
            {isFromSettings ? 'Понятно!' : 'Вперед!'}
          </Text>
        </TouchableOpacity>
      </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    flexDirection: 'column',
    backgroundColor: '#ffffff',
    paddingHorizontal: 24,
    justifyContent: 'center',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-around',
    alignItems: 'center',
    marginBottom: 30,
  },
  logo: {
    width: 200,
    height: 100,
    resizeMode: 'contain', 
  },
  appName: {
    fontSize: 28,
    fontWeight: 'bold',
  },
  aboutTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 40,
    textAlign: 'center',
  },
  aboutText: {
    fontSize: 18,
    fontWeight: '500',
    lineHeight: 28,
  },
  forwardButton: {
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 30,
  },
  forwardButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default About;