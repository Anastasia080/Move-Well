import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import LoginScreen from './src/components/LoginScreen';
import RegisterScreen from './src/components/RegisterScreen';
import About from './src/components/About';
import Profile from './src/components/Profile';
import Main from './src/components/Main';
import Favorite from './src/components/Favorite';
import Settings from './src/components/Settings';
import ShowVideo from './src/components/ShowVideo';
import Legs from './src/components/Category/Legs';
import Hands from './src/components/Category/Hands';
import Body from './src/components/Category/Body';
import All from './src/components/Category/All';
import { ThemeProvider } from './src/components/ThemeContext';
import ExerciseSession from './src/components/ExerciseSession';

const Stack = createNativeStackNavigator();

const App = () => {
  return (
    <ThemeProvider>
      <NavigationContainer>
        <Stack.Navigator initialRouteName="Login">
          <Stack.Screen
            name="Login"
            component={LoginScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="Register"
            component={RegisterScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="About"
            component={About}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="Profile"
            component={Profile}
            options={{ headerShown: false }}
            initialParams={{ isNewUser: false }}
          />
          <Stack.Screen
            name="Main"
            component={Main}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="Favorite"
            component={Favorite}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="Settings"
            component={Settings}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="ShowVideo"
            component={ShowVideo}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="ExerciseSession"
            component={ExerciseSession}
            options={{ headerShown: false }}
          />

          <Stack.Screen
            name="Legs"
            component={Legs}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="Hands"
            component={Hands}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="Body"
            component={Body}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="All"
            component={All}
            options={{ headerShown: false }}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </ThemeProvider>
  );
};

export default App;
