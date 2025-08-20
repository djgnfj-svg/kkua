import { create } from 'zustand';
import type { GameRoom, GameState } from '../types/game';

interface GameStoreState {
  // Game Room
  currentRoom: GameRoom | null;
  rooms: GameRoom[];
  
  // Game State
  gameState: GameState | null;
  
  // UI State
  isLoading: boolean;
  error: string | null;
}

interface GameStoreActions {
  // Room Actions
  setCurrentRoom: (room: GameRoom | null) => void;
  setRooms: (rooms: GameRoom[]) => void;
  updateRoom: (roomId: string, updates: Partial<GameRoom>) => void;
  
  // Game Actions
  setGameState: (gameState: GameState | null) => void;
  updateGameState: (updates: Partial<GameState>) => void;
  addWordToChain: (word: string) => void;
  
  // UI Actions
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useGameStore = create<GameStoreState & GameStoreActions>((set) => ({
  // State
  currentRoom: null,
  rooms: [],
  gameState: null,
  isLoading: false,
  error: null,

  // Room Actions
  setCurrentRoom: (currentRoom) => set({ currentRoom }),
  
  setRooms: (rooms) => set({ rooms }),
  
  updateRoom: (roomId, updates) => 
    set((state) => ({
      rooms: state.rooms.map(room => 
        room.id === roomId ? { ...room, ...updates } : room
      ),
      currentRoom: state.currentRoom?.id === roomId 
        ? { ...state.currentRoom, ...updates } 
        : state.currentRoom
    })),

  // Game Actions
  setGameState: (gameState) => set({ gameState }),
  
  updateGameState: (updates) =>
    set((state) => ({
      gameState: state.gameState 
        ? { ...state.gameState, ...updates }
        : null
    })),
  
  addWordToChain: (word) =>
    set((state) => ({
      gameState: state.gameState
        ? {
            ...state.gameState,
            wordChain: [...state.gameState.wordChain, word],
            currentWord: word
          }
        : null
    })),

  // UI Actions
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));