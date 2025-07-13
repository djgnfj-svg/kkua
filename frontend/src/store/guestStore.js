import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const guestStore = create(
  // persist 임시 비활성화 - 새로고침 문제 해결용
  // persist(
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
    })
    // persist 설정 임시 주석처리
    // ,{
    //   name: 'guest-storage',
    //   getStorage: () => localStorage,
    //   partialize: (state) => ({
    //     nickname: state.nickname,
    //     preferences: state.preferences,
    //     gameHistory: state.gameHistory,
    //   }),
    // }
  // )
);

export default guestStore;
