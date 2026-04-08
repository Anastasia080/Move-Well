import React, { createContext, useContext, useState, ReactNode } from 'react';

interface Video {
  id: number;
  title: string;
  description: string;
}

interface FavoriteContextType {
  favorites: Video[];
  toggleFavorite: (video: Video) => void;
  isFavorite: (videoId: number) => boolean;
}

const FavoriteContext = createContext<FavoriteContextType | undefined>(undefined);

export const FavoriteProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [favorites, setFavorites] = useState<Video[]>([]);

  const toggleFavorite = (video: Video) => {
    setFavorites(prev => {
      const exists = prev.find(v => v.id === video.id);
      if (exists) {
        return prev.filter(v => v.id !== video.id);
      } else {
        return [...prev, video];
      }
    });
  };

  const isFavorite = (videoId: number) => {
    return favorites.some(video => video.id === videoId);
  };

  return (
    <FavoriteContext.Provider value={{ favorites, toggleFavorite, isFavorite }}>
      {children}
    </FavoriteContext.Provider>
  );
};

export const useFavorite = () => {
  const context = useContext(FavoriteContext);
  if (!context) {
    throw new Error('useFavorite must be used within a FavoriteProvider');
  }
  return context;
};