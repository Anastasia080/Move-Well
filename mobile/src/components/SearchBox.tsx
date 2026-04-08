import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  Image,
  TouchableOpacity,
} from 'react-native';
import { useTheme } from './ThemeContext';

type SearchBoxProps = {
  value: string;
  onChangeText: (text: string) => void;
  onSearch?: () => void;
  onClear?: () => void;
  placeholder?: string;
};

const SearchBox = ({ 
  value, 
  onChangeText, 
  onSearch, 
  onClear,
  placeholder = "Поиск"
}: SearchBoxProps) => {
  const { colors } = useTheme();

  const handlePress = () => {
    if (value.trim()) {
      onClear?.();
    } else {
      onSearch?.();
    }
  };

return (
    <View style={styles.searchBox}>
      <TextInput
        style={[styles.searchInput, { 
          backgroundColor: colors.card,
          borderColor: colors.border,
          color: colors.text 
        }]}
        placeholder={placeholder}
        value={value}
        onChangeText={onChangeText}
        placeholderTextColor={colors.placeholder}
        returnKeyType="search"
        onSubmitEditing={onSearch}
      />
      <TouchableOpacity 
        style={styles.interfaceButton} 
        onPress={handlePress}
      >
        <Image 
          source={value.trim() 
            ? require('../assets/icons/close.png') 
            : require('../assets/icons/search.png')} 
          style={[styles.searchIcon, { tintColor: colors.buttonOutlineText }]}
        />
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  searchBox: {
    display: 'flex',
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    marginTop: 60,
    marginBottom: 20,
  },
  searchInput: {
    flex: 1,
    borderRadius: 12,
    paddingHorizontal: 16,
    fontSize: 16,
    borderWidth: 1,
    height: 50,
  },
  interfaceButton: {
    backgroundColor: 'transparent',
    paddingVertical: 16,
    paddingHorizontal: 10,
    alignItems: 'center',
  },
  searchIcon: {
    width: 24,
    height: 24,
  },
});

export default SearchBox;