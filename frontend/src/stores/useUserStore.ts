import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: string;
  nickname: string;
  isGuest: boolean;
  sessionToken?: string;
}

interface UserState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface UserActions {
  setUser: (user: User) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useUserStore = create<UserState & UserActions>()(
  persist(
    (set) => ({
      // State
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      setUser: (user: User) =>
        set({ 
          user, 
          isAuthenticated: true, 
          error: null 
        }),

      logout: () =>
        set({ 
          user: null, 
          isAuthenticated: false, 
          error: null 
        }),

      setLoading: (isLoading: boolean) =>
        set({ isLoading }),

      setError: (error: string | null) =>
        set({ error }),

      clearError: () =>
        set({ error: null }),
    }),
    {
      name: 'kkua-user-storage',
      partialize: (state) => ({ 
        user: state.user, 
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
);