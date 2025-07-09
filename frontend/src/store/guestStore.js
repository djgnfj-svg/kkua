import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Simplified guest store focused on guest-specific data only
// Authentication is now handled by AuthContext
const guestStore = create(
  persist(
    (set, get) => ({
      // Guest profile information
      nickname: '',
      lastLogin: null,
      preferences: {
        notifications: true,
        sound: true,
      },

      // Game-related state
      activeGameId: null,
      gameHistory: [],

      // Actions
      setNickname: (nickname) =>
        set(() => ({
          nickname,
        })),

      setPreferences: (preferences) =>
        set(() => ({
          preferences: { ...get().preferences, ...preferences },
        })),

      setActiveGame: (gameId) =>
        set(() => ({
          activeGameId: gameId,
        })),

      addToGameHistory: (gameData) =>
        set((state) => ({
          gameHistory: [gameData, ...state.gameHistory.slice(0, 9)], // Keep last 10 games
        })),

      resetGuestData: () =>
        set(() => ({
          nickname: '',
          lastLogin: null,
          activeGameId: null,
          gameHistory: [],
          preferences: {
            notifications: true,
            sound: true,
          },
        })),
    }),
    {
      name: 'guest-storage',
      getStorage: () => localStorage,
      partialize: (state) => ({
        nickname: state.nickname,
        preferences: state.preferences,
        gameHistory: state.gameHistory,
      }),
    }
  )
);

export default guestStore;