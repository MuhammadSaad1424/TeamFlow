import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  github_username: string;
  email: string;
  display_name?: string;
  avatar_url?: string;
  subscription_tier: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
}

interface AppState {
  selectedRepositoryId: string | null;
  setSelectedRepository: (id: string | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      setAuth: (user, accessToken, refreshToken) => {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
        set({ user, accessToken, isAuthenticated: true });
      },
      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({ user: null, accessToken: null, isAuthenticated: false });
      },
    }),
    { name: 'teamflow-auth' },
  ),
);

export const useAppStore = create<AppState>((set) => ({
  selectedRepositoryId: null,
  setSelectedRepository: (id) => set({ selectedRepositoryId: id }),
}));
