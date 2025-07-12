import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const guestStore = create(
  persist(
    (set, get) => ({
      nickname: '',
      lastLogin: null,
      preferences: {
        notifications: true,
        sound: true,
      },

      activeGameId: null,
      gameHistory: [],

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
          gameHistory: [gameData, ...state.gameHistory.slice(0, 9)],
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
