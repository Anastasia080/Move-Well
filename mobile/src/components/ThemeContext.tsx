import React, { createContext, useContext, useState, ReactNode} from 'react';

type ThemeType = 'light' | 'dark';

interface ThemeColors {
  background: string;
  text: string;
  primary: string;
  card: string;
  border: string;
  buttonBg: string;
  buttonText: string;
  buttonOutline: string;
  buttonOutlineText: string;
  sliderTrack: string;
  placeholder: string;
}

interface ThemeContextType {
  theme: ThemeType;
  colors: ThemeColors;
  toggleTheme: () => void;
  setThemeFromServer: (theme: string) => void;
  getCurrentTheme: () => ThemeType;
}

const lightColors: ThemeColors = {
  background: '#ffffff',
  text: '#333333',
  primary: '#4CAF50',
  card: '#f1efefff',
  border: '#e0e0e0',
  buttonBg: '#4CAF50',
  buttonText: '#ffffff',
  buttonOutline: '#4CAF50',
  buttonOutlineText: '#4CAF50',
  sliderTrack: '#e0e0e0',
  placeholder: '#999999',
};

const darkColors: ThemeColors = {
  background: '#121212',
  text: '#ffffff',
  primary: '#4CAF50',
  card: '#1e1e1e',
  border: '#333333',
  buttonBg: '#4CAF50',
  buttonText: '#ffffff',
  buttonOutline: '#4CAF50',
  buttonOutlineText: '#ffffff',
  sliderTrack: '#333333',
  placeholder: '#999999',
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<ThemeType>('light');
  const [colors, setColors] = useState<ThemeColors>(lightColors);

  const setThemeFromServer = (serverTheme: string) => {
    if (serverTheme === 'dark') {
      setTheme('dark');
      setColors(darkColors);
    } else {
      setTheme('light');
      setColors(lightColors);
    }
  };

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    setColors(newTheme === 'light' ? lightColors : darkColors);
  };

  const getCurrentTheme = () => theme;

  return (
    <ThemeContext.Provider value={{ theme, colors, toggleTheme, setThemeFromServer, getCurrentTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};