import React, {useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  Image,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useNavigation, useRoute } from '@react-navigation/native';
import BottomMenu from './BottomMenu';
import { useTheme } from './ThemeContext';
import { useFavorite } from './FavoriteContext';

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
type ShowVideoScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'ShowVideo'>;

const ShowVideo = () => {
  const navigation = useNavigation<ShowVideoScreenNavigationProp>();
  const route = useRoute();
  const { colors } = useTheme();
  const { toggleFavorite, isFavorite } = useFavorite();

  const video = (route.params as any)?.video as Video;
  if (!video) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <Text style={{ color: colors.text }}>Видео не найдено</Text>
        <BottomMenu />
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>

        <View style = {styles.headermenu}>
            <TouchableOpacity style = {styles.backButton} onPress= {() => navigation.goBack()}>
                <Image 
                    source={require('../assets/icons/left-arrow.png')} 
                    style={[styles.backIcon, { tintColor: colors.primary }]}
                />
            </TouchableOpacity>

            <TouchableOpacity style={styles.heartButton} onPress={() => toggleFavorite(video)}>
                <Image 
                    source={isFavorite(video.id) 
                            ? require('../assets/icons/favorite.png') 
                            : require('../assets/icons/add-to-favorites.png')} 
                    style={[styles.heartIcon, {tintColor: colors.primary }]}
                />
            </TouchableOpacity>
        </View>
        
        <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent} 
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        >
          <View style={[styles.videoPlaceholder, { backgroundColor: colors.card }]}>
              <Text style={[styles.videoPlaceholderText, { color: colors.text }]}>
                  Видео {video.id}
              </Text>
                                
          </View>
          <Text style={[styles.videoTitle, { color: colors.text }]}>
              {video.title}
          </Text>
          <Text style={[styles.videoDescription, { color: colors.text }]}>
              {video.description}
          </Text>

          <Text style={[styles.disclaimer, { color: colors.text }]}>
              Видео и информация несут рекомендательный характер и не являются леченем. 
              Необходима консультация со специалистом.
          </Text>
          
        </ScrollView>

        <TouchableOpacity style={[styles.startButton, { backgroundColor: colors.buttonBg }]}>
            <Text style={[styles.startButtonText, { color: colors.buttonText }]}>
              Начать
            </Text>
        </TouchableOpacity>
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
  scrollContent: {
    paddingBottom: 100,
    paddingTop: 20,
  },
  headermenu: {
    display: 'flex',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 70,
    marginBottom: 20,
  },
  videoPlaceholder: {
    width: '100%',
    aspectRatio: 16/10,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 30,
  },
  videoPlaceholderText: {
    fontSize: 20,
  },
  videoTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 50,
  },
  videoDescription: {
    fontSize: 20,
    marginBottom: 50,
  },
  disclaimer: {
    fontSize: 14,
    color: '#c4c2c2',
  },
  heartButton: {
    width: 34,
    height: 34,
    backgroundColor: 'transparent',
    justifyContent: 'center',
    alignItems: 'center',
  },
  heartIcon: {
    width: 34,
    height: 34,
  },
  backButton: {
    width: 34,
    height: 34,
    backgroundColor: 'transparent',
    justifyContent: 'center',
    alignItems: 'center',
  },
  backIcon: {
    width: 34,
    height: 34,
  },
  startButton: {
    width: '100%',
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 20,
    alignItems: 'center',
    marginBottom: 120,
  },
  startButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default ShowVideo;