import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Image,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useNavigation } from '@react-navigation/native';
import BottomMenu from '../BottomMenu';
import { useTheme } from '../ThemeContext';
import { useFavorite } from '../FavoriteContext';
import SearchBox from '../SearchBox';

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
  All: undefined;
  ShowVideo: { video: Video };
};
type AllScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'All'>;

const All = () => {
  const navigation = useNavigation<AllScreenNavigationProp>();
  const { colors } = useTheme();
  const [search, setSearch] = useState('');
  const { toggleFavorite, isFavorite } = useFavorite();
  const [showSearchResults, setShowSearchResults] = useState(false);

  const videos = [
    { id: 1, title: 'Видео 1', description: 'Описание видео 1' },
    { id: 2, title: 'Видео 2', description: 'Описание видео 2' },
    { id: 3, title: 'Видео 3', description: 'Описание видео 3' },
    { id: 4, title: 'Видео 4', description: 'Описание видео 4' },
    { id: 5, title: 'Видео 5', description: 'Описание видео 5' },
    { id: 6, title: 'Видео 6', description: 'Описание видео 6' },
    { id: 7, title: 'Видео 7', description: 'Описание видео 7' },
    { id: 8, title: 'Видео 8', description: 'Описание видео 8' },
    { id: 9, title: 'Видео 9', description: 'Описание видео 9' },
    { id: 10, title: 'Видео 10', description: 'Описание видео 10' },
    { id: 11, title: 'Видео 11', description: 'Описание видео 11' },
    { id: 12, title: 'Видео 12', description: 'Описание видео 12' },
  ];

  const filteredVideos = useMemo(() => {
    if (!search.trim()) {
      return videos.slice(0, 12);
    }
    
    const query = search.toLowerCase().trim();
    return videos.filter(video => 
      video.title.toLowerCase().includes(query) ||
      video.description.toLowerCase().includes(query)
    );
  }, [search]);

  const videosToShow = search.trim() ? filteredVideos : videos.slice(0, 12);

 const handleChangeText = (text: string) => {
    setSearch(text);
    setShowSearchResults(!!text.trim());
  };

  const handleSearch = () => {
    if (search.trim()) {
      console.log('Поиск:', search);
    }
  };

  const handleClear = () => {
    setSearch('');
    setShowSearchResults(false);
  };

  const handleVideoPress = (video: Video) => {
  navigation.navigate('ShowVideo', { video });
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
        <SearchBox 
        value={search}
        onChangeText={handleChangeText}
        onSearch={handleSearch}
        onClear={handleClear}
        />
        
        <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent} 
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        >
            
          {showSearchResults && search.trim() ? (
            <View style={styles.section}>
              <View style={styles.searchResultsHeader}>
                <Text style={[styles.searchResultsTitle, { color: colors.text }]}>
                  Результаты поиска
                </Text>
                <Text style={[styles.resultsCount, { color: colors.primary }]}>
                  Найдено: {filteredVideos.length}
                </Text>
              </View>
              
              {filteredVideos.length === 0 ? (
                <View style={styles.noResultsContainer}>
                  <Text style={[styles.noResultsText, { color: colors.text }]}>
                    По запросу "{search}" ничего не найдено
                  </Text>
                </View>
            ) : (
              <View style={styles.videosGrid}>
                {filteredVideos.map((video) => (
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
                        onPress={(e) => {
                          e.stopPropagation();
                          toggleFavorite(video);
                        }}
                      >
                        <Image 
                          source={isFavorite(video.id) 
                            ? require('../../assets/icons/favorite.png') 
                            : require('../../assets/icons/add-to-favorites.png')} 
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
        ) : (
          <>
            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>Все видео</Text>
              <View style={styles.videosGrid}>
                {videosToShow.map((video) => (
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
                        onPress={(e) => {
                          e.stopPropagation();
                          toggleFavorite(video);
                        }}
                      >
                        <Image 
                          source={isFavorite(video.id) 
                            ? require('../../assets/icons/favorite.png') 
                            : require('../../assets/icons/add-to-favorites.png')} 
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
            </View>
          </>
        )}
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
  scrollView: {
    flex: 1,
  },
  section: {
    display: 'flex',
    flexDirection: 'column',
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  scrollContent: {
    paddingBottom: 100,
    paddingTop: 20,
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
  searchResultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  searchResultsTitle: {
    fontSize: 22,
    fontWeight: 'bold',
  },
  resultsCount: {
    fontSize: 16,
    fontWeight: '600',
  },
  noResultsContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  noResultsText: {
    fontSize: 16,
    textAlign: 'center',
  },
});

export default All;