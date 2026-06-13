import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  Image,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useNavigation } from '@react-navigation/native';
import BottomMenu from './BottomMenu';
import { useTheme } from './ThemeContext';
import { useFavorite } from './FavoriteContext';
import SearchBox from './SearchBox';

type Video = {
  id: number;
  title: string;
  description: string;
};

type RootStackParamList = {
  Profile: undefined;
  Main: undefined;
  Favorite: undefined;
  Settings: undefined;
  ShowVideo: { video: Video };
};
type FavoriteScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Favorite'>;

const Favorite = () => {
  const navigation = useNavigation<FavoriteScreenNavigationProp>();
  const [search, setSearch] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const { favorites, toggleFavorite } = useFavorite();
  const { colors } = useTheme();

   const filteredFavorites = useMemo(() => {
    if (!search.trim()) {
      return favorites;
    }
    
    const query = search.toLowerCase().trim();
    return favorites.filter(video => 
      video.title.toLowerCase().includes(query) ||
      video.description.toLowerCase().includes(query)
    );
  }, [favorites, search]);

  const handleSearch = () => {
    console.log('Поиск в избранном:', search);
  };

  const toggleDropDown = () =>{
    setIsOpen(!isOpen);
  };

  const handleVideoPress = (video: Video) => {
  navigation.navigate('ShowVideo', { video });
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
        <View style={styles.searchBox}>
              <TextInput
                        style={[styles.searchInput, { 
                                backgroundColor: colors.card,
                                borderColor: colors.border,
                                color: colors.text 
                              }]}
                        placeholder="Поиск в избранном"
                        value={search}
                        onChangeText={setSearch}
                        placeholderTextColor={colors.placeholder}
                        autoFocus={false}
                />
              <TouchableOpacity style={styles.interfaceButton} onPress={handleSearch}>
                  <Image 
                    source={require('../assets/icons/search.png')} 
                    style={[styles.searchIcon, { tintColor: colors.buttonOutlineText }]}
                  />
              </TouchableOpacity>
        </View>
        
        <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent} 
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        >
            <View style={styles.section}>
              <View style={styles.favoriteSectionTitle}>
                <Text style={[styles.favoriteTitleText, { color: colors.text }]}>
                  Избранные видео {favorites.length > 0 ? `(${favorites.length})` : ''}
                </Text>
                <TouchableOpacity style={styles.interfaceButton} onPress={toggleDropDown}>
                  <Image 
                    source={require('../assets/icons/filter.png')} 
                    style={[styles.searchIcon, { tintColor: colors.buttonOutlineText }]}
                  />
                </TouchableOpacity>
              </View>
              
              {favorites.length === 0 ? (
                <View style={styles.emptyContainer}>
                  <Image 
                    source={require('../assets/icons/favorite.png')} 
                    style={[styles.emptyIcon, { tintColor: colors.primary }]}
                  />
                  <Text style={[styles.emptyText, { color: colors.text }]}>
                    Нет избранных видео
                  </Text>
                  <Text style={[styles.emptySubtext, { color: colors.text }]}>
                    Добавляйте видео, нажимая на сердечко
                  </Text>
                </View>
              ) : filteredFavorites.length === 0 ? (
                <View style={styles.emptyContainer}>
                  <Text style={[styles.emptyText, { color: colors.text }]}>
                    По запросу "{search}" ничего не найдено
                  </Text>
                </View>
              ) : (
                <View style={styles.videosGrid}>
                  {filteredFavorites.map((video) => (
                    <TouchableOpacity 
                      key={video.id} 
                      style={styles.videoCard}
                      onPress= {() => handleVideoPress(video)}
                      activeOpacity={0.7}
                    >
                      <View style={[styles.videoPlaceholder, { backgroundColor: colors.card }]}>
                        <Text style={[styles.videoPlaceholderText, { color: colors.text }]}>
                          Видео {video.id}
                        </Text>
                        <TouchableOpacity 
                          style={styles.heartButton}
                          onPress={() => toggleFavorite(video)}
                        >
                          <Image 
                            source={require('../assets/icons/favorite.png')} 
                            style={[styles.heartIcon, { 
                              tintColor: colors.primary 
                            }]}
                          />
                        </TouchableOpacity>
                      </View>
                      <Text style={[styles.videoTitle, { color: colors.text }]}>
                        {video.title}
                      </Text>
                      <Text style={[styles.videoDescription, { color: colors.text }]}>
                        {video.description}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              )}
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
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 100,
    paddingTop: 20,
  },
  section: {
    display: 'flex',
    flexDirection: 'column',
  },
  favoriteSectionTitle: {
    display:'flex',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  favoriteTitleText: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  videosGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  videoCard: {
    width: '48%',
    marginBottom: 20,
  },
  videoPlaceholder: {
    width: '100%',
    aspectRatio: 16/9,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
    position: 'relative',
  },
  videoPlaceholderText: {
    fontSize: 14,
  },
  videoTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  videoDescription: {
    fontSize: 14,
  },
  heartButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 32,
    height: 32,
    backgroundColor: 'transparent',
    justifyContent: 'center',
    alignItems: 'center',
  },
  heartIcon: {
    width: 24,
    height: 24,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyIcon: {
    width: 60,
    height: 60,
    marginBottom: 20,
    opacity: 0.5,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
    textAlign: 'center',
  },
  emptySubtext: {
    fontSize: 14,
    textAlign: 'center',
    opacity: 0.7,
  },
});

export default Favorite;