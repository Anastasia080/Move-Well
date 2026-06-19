import AsyncStorage from '@react-native-async-storage/async-storage';
import { jwtDecode } from 'jwt-decode';

import { Platform } from 'react-native';

const getApiUrl = () => {
  if (__DEV__) {
    if (Platform.OS === 'android') {
      // 10.0.2.2 — только для эмулятора. Для реального устройства нужен IP Mac в локальной сети.
      // Узнать IP: ifconfig | grep "inet " | grep -v 127.0.0.1
      return 'http://172.20.10.11:8000';
    }
    return 'http://localhost:8000';
  }
  return 'https://your-production-api.com';
};

export const API_BASE_URL = getApiUrl();

export interface UserData {
  email: string;
  password: string;
  diagnosis?: string[];
  mobility_limits?: string[];
}

export interface AuthResponse {
  access_token: string;
}

export interface UserProfile {
  user_id: string;
  email: string;
  diagnosis: string[];
  mobility_limits: string[];
  theme: string;
  created_at: string;
  last_login: string | null;
}

export interface UpdateProfileData {
  diagnosis?: string[];
  mobility_limits?: string[];
  theme?: string;
}

export interface Exercise {
  id: string;
  title: string;
  description: string;
  category: string;
  video_url: string | null;
  duration_sec: number | null;
  key_points: string[];
  is_favorite: number;
}

interface JWTPayload {
  sub: string;
  exp?: number;
  iat?: number;
}

class ApiService {
  private async request<T>(
    endpoint: string,
    method: string = 'GET',
    body?: any,
    requireAuth: boolean = false,
    expectEmptyResponse: boolean = false,
  ): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (requireAuth) {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) {
        throw new Error('No authentication token found');
      }
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config: RequestInit = {
      method,
      headers,
    };

    if (body) {
      config.body = JSON.stringify(body);
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API Error: ${response.status}`);
    }

    if (expectEmptyResponse || response.status === 204) {
      return {} as T;
    }

    return response.json();
  }
  //Auth
  async register(userData: UserData): Promise<AuthResponse> {
    return this.request<AuthResponse>('/auth/register', 'POST', userData);
  }

  async login(email: string, password: string): Promise<AuthResponse> {
    return this.request<AuthResponse>('/auth/login', 'POST', {
      email,
      password,
    });
  }

  async logout(): Promise<void> {
    await AsyncStorage.removeItem('access_token');
    await AsyncStorage.removeItem('user_email');
  }

  //Profile
  async getProfile(): Promise<UserProfile> {
    return this.request<UserProfile>('/profile', 'GET', undefined, true);
  }

  async updateProfile(data: UpdateProfileData): Promise<UserProfile> {
    return this.request<UserProfile>('/profile', 'PUT', data, true);
  }

  async deleteAccount(confirmation: boolean = true): Promise<void> {
    return this.request<void>(
      '/profile?confirmation=' + confirmation,
      'DELETE',
      undefined,
      true,
    );
  }

  async getCurrentUserId(): Promise<string | null> {
    try {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) return null;

      const decoded = jwtDecode<JWTPayload>(token);
      return decoded.sub;
    } catch (error) {
      console.error('Error decoding token:', error);
      return null;
    }
  }

  async isAuthenticated(): Promise<boolean> {
    const token = await AsyncStorage.getItem('access_token');
    if (!token) return false;
    try {
      const decoded = jwtDecode<JWTPayload>(token);
      if (decoded.exp && decoded.exp < Date.now() / 1000) {
        await this.logout();
        return false;
      }
      return true;
    } catch {
      return false;
    }
  }

  async saveAuthData(token: string, email: string): Promise<void> {
    await AsyncStorage.setItem('access_token', token);
    await AsyncStorage.setItem('user_email', email);
  }

  async updateTheme(theme: string): Promise<UserProfile> {
    console.log('🔵 updateTheme called with theme:', theme);
    const token = await AsyncStorage.getItem('access_token');
    console.log('🔵 Token exists:', !!token);
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE_URL}/profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ theme }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API Error: ${response.status}`);
    }

    return response.json();
  }

  //Exercise
  async getExercises(category?: string, search?: string): Promise<Exercise[]> {
    let url = '/exercises';
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (search) params.append('search', search);
    if (params.toString()) url += `?${params.toString()}`;
    return this.request<Exercise[]>(url, 'GET', undefined, true);
  }

  async getExerciseById(id: string): Promise<Exercise> {
    return this.request<Exercise>(`/exercises/${id}`, 'GET', undefined, true);
  }

  async addToFavorites(exerciseId: string): Promise<void> {
    return this.request<void>(
      `/exercises/${exerciseId}/favorite`,
      'POST',
      undefined,
      true,
    );
  }

  async removeFromFavorites(exerciseId: string): Promise<void> {
    return this.request<void>(
      `/exercises/${exerciseId}/favorite`,
      'DELETE',
      undefined,
      true,
      true,
    );
  }

  async getFavorites(): Promise<Exercise[]> {
    return this.request<Exercise[]>(
      '/exercises/favorites/list',
      'GET',
      undefined,
      true,
    );
  }

  async getCategories(): Promise<{ categories: string[] }> {
    return this.request<{ categories: string[] }>(
      '/exercises/categories/list',
      'GET',
      undefined,
      true,
    );
  }

  async getRecommended(): Promise<Exercise[]> {
    return this.request<Exercise[]>(
      '/exercises/recommended',
      'GET',
      undefined,
      true,
    );
  }
}

export const apiService = new ApiService();
export default apiService;
