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
  Main: undefined;
};
type LoginScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Login'>;

const LoginScreen = () => {
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const navigation = useNavigation<LoginScreenNavigationProp>();

  const handleLogin = () => {
    console.log('Логин:', login);
    console.log('Пароль:', password);
    navigation.navigate('Main');
  };

  const handleRegister = () => {
    navigation.navigate('Register');
  }

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

        <TouchableOpacity style={styles.loginButton} onPress={handleLogin}>
          <Text style={styles.loginButtonText}>Вход</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.registerLink} onPress={handleRegister}>
          <Text style={styles.registerLinkText}>Зарегистрироваться</Text>
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
    marginBottom: 50,
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
  loginButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  loginButtonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  registerLink: {
    alignItems: 'center',
    marginTop: 16,
  },
  registerLinkText: {
    color: '#4CAF50',
    fontSize: 18,
    fontWeight: 'bold',
    textDecorationLine: 'none',
  },
});

export default LoginScreen;