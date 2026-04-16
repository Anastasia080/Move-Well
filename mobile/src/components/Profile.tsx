import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useNavigation } from '@react-navigation/native';
import  Slider  from '@react-native-community/slider';
import { useTheme } from './ThemeContext';

type RootStackParamList = {
  Main: undefined;
};
type MainScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Main'>;

const Profile = () => {
  const navigation = useNavigation<MainScreenNavigationProp>();
  const { colors } = useTheme();
  const handleMain = () => {
    navigation.navigate('Main');
  };
  
  const [mobilityValue, setMobilityValue] = useState(1);

  const getLevelText = (value: number) => {
    if (value === 0) return 'Низкий';
    if (value === 1) return 'Средний';
    return 'Высокий';
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>

        <Text style={[styles.profileTitle, { color: colors.text }]}>Профиль</Text>

        <Text style={[styles.loginText, {color: colors.text,borderColor: colors.primary}]}>Логин</Text>

        <View style={[styles.profileInfo, {borderColor: colors.primary}]}>

          <Text style={[styles.profileInfoText, { color: colors.text }]}>Тип ограничения подвижности</Text>
          <Text>-</Text>
          <Text>-</Text>
          <Text>-</Text>
          <Text>-</Text>

          <Text style={[styles.profileInfoText, { color: colors.text }]}>Уровень подвижности</Text>
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
              <Text style={[styles.label, { color: colors.text }]}>Средний</Text>
              <Text style={[styles.label, { color: colors.text }]}>Высокий</Text>
            </View>
        
            <Text style={[styles.currentLevel, { color: colors.primary }]}>
              Текущий уровень: {getLevelText(mobilityValue)}
            </Text>
          </View>

        </View>

        <View style={styles.buttonProfile}>

          <TouchableOpacity style={[styles.resetButton, {borderColor: colors.primary}]}>
            <Text style={[styles.resetButtonText, { color: colors.primary }]}>Сбросить</Text>
          </TouchableOpacity>

          <TouchableOpacity style={[styles.saveButton, { backgroundColor: colors.primary }]} onPress={handleMain}>
            <Text style={[styles.saveButtonText, { color: colors.buttonText }]}>Сохранить</Text>
          </TouchableOpacity>

        </View>

      </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    display: 'flex',
    gap: 40,
    flexDirection: 'column',
    paddingHorizontal: 24,
    justifyContent: 'center',
  },
  profileTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  loginText: {
    fontSize: 18,
    fontWeight: '500',
    borderWidth: 2,
    borderRadius: 12,
    paddingHorizontal: 20,
    paddingVertical: 10,
    textAlign: 'center',
    width: '100%',
  },
  profileInfo: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    gap: 30,
    borderWidth: 2,
    borderRadius: 12,
    paddingHorizontal: 20,
    paddingVertical: 15,
    width: '100%',
  },
  profileInfoText: {
    fontSize: 18,
    fontWeight: 'bold',
    textAlign: 'left',
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
  buttonProfile: {
    display:'flex',
    flexDirection:'row',
    justifyContent: 'space-around',
    marginTop: 30,
  },
  saveButton: {
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  saveButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  resetButton: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  resetButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default Profile;