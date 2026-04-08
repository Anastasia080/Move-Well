import React from 'react';
import {
  View,
  TouchableOpacity,
  Image,
  StyleSheet,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useTheme } from './ThemeContext';

type RootStackParamList = {
  Profile: undefined;
  Main: undefined;
  Favorite: undefined;
  Settings: undefined;
};

type BottomMenuNavigationProp = NativeStackNavigationProp<RootStackParamList>;

const BottomMenu = () => {
  const navigation = useNavigation<BottomMenuNavigationProp>();
  const { colors, theme } = useTheme();

  const handleMain = () => {
    navigation.navigate('Main');
  };

  const handleFavorite = () => {
    navigation.navigate('Favorite');
  };

  const handleProfile = () => {
    navigation.navigate('Profile');
  };

  const handleSettings = () => {
    navigation.navigate('Settings');
  };

  const getIconTintColor = () => {
    return theme === 'dark' ? '#ffffff' : '#4CAF50';
  };

  return (
    <View style={styles.menuContainer}>
      <View style={[
        styles.menuBottomBox,
        { 
          backgroundColor: colors.background,
          borderColor: theme === 'dark' ? '#444444' : '#e0e0e0',
          shadowColor: theme === 'dark' ? '#000000' : '#000000',
          shadowOpacity: theme === 'dark' ? 0.4 : 0.1,
          shadowRadius: theme === 'dark' ? 8 : 4,
          ...(theme === 'dark' && {
            elevation: 10,
            borderWidth: 1,
            borderColor: '#333333',
          })
        }
      ]}>
        <TouchableOpacity style={styles.interfaceButton} onPress={handleMain}>
          <Image 
            source={require('../assets/icons/home.png')} 
            style={[styles.menuIcon, { tintColor: getIconTintColor() }]}
          />
        </TouchableOpacity>
        <TouchableOpacity style={styles.interfaceButton} onPress={handleFavorite}>
          <Image 
            source={require('../assets/icons/favorite.png')} 
            style={[styles.menuIcon, { tintColor: getIconTintColor() }]}
          />
        </TouchableOpacity>
        <TouchableOpacity style={styles.interfaceButton} onPress={handleProfile}>
          <Image 
            source={require('../assets/icons/user.png')} 
            style={[styles.menuIcon, { tintColor: getIconTintColor() }]}
          />
        </TouchableOpacity>
        <TouchableOpacity style={styles.interfaceButton} onPress={handleSettings}>
          <Image 
            source={require('../assets/icons/settings.png')} 
            style={[styles.menuIcon, { tintColor: getIconTintColor() }]}
          />
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  menuContainer: {
    position: 'absolute',
    bottom: 10,
    left: 0,
    right: 0,
    paddingHorizontal: 24,
    paddingBottom: 20,
  },
  menuBottomBox: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    borderWidth: 1,
    borderRadius: 12,
    paddingVertical: 10,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  interfaceButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  menuIcon: {
    width: 30,
    height: 30,
  },
});

export default BottomMenu;