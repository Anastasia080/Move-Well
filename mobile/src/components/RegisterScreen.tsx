import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Image,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useNavigation } from '@react-navigation/native';

type RootStackParamList = {
  Login: undefined;
  Register: undefined;
  About: undefined;
};

type RegisterScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Register'>;

const RegisterScreen = () => {
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const navigation = useNavigation<RegisterScreenNavigationProp>();

  const handleRegister = () => {
    console.log('Регистрация - Логин:', login);
    console.log('Пароль:', password);
    console.log('Подтверждение пароля:', confirmPassword);
    navigation.navigate('About');
  };

  const handleBackToLogin = () => {
    navigation.navigate('Login');
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Image 
          source={require('../assets/logo.png')} 
          style={styles.logo} 
        />
        <Text style={styles.appName}>Move Well</Text>
      </View>

      <View style={styles.form}>

        <Text style={styles.registerTitle}>Регистрация</Text>

        <TextInput
          style={styles.input}
          placeholder="Логин"
          value={login}
          onChangeText={setLogin}
          placeholderTextColor="#999"
        />
        
        <TextInput
          style={styles.input}
          placeholder="Пароль"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          placeholderTextColor="#999"
        />

        <TextInput
          style={styles.input}
          placeholder="Повторите пароль"
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          secureTextEntry
          placeholderTextColor="#999"
        />

        <TouchableOpacity style={styles.registerButton} onPress={handleRegister}>
          <Text style={styles.registerButtonText}>Зарегистрироваться</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.loginLink} onPress={handleBackToLogin}>
          <Text style={styles.loginLinkText}>Уже есть аккаунт? Войти</Text>
        </TouchableOpacity>
      </View>
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
    color: '#333',
  },
  registerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
  },
  form: {
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
  },
  input: {
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  registerButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  registerButtonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  loginLink: {
    alignItems: 'center',
    marginTop: 16,
  },
  loginLinkText: {
    color: '#4CAF50',
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default RegisterScreen;