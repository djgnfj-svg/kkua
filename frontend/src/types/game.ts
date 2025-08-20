export interface GameRoom {
  id: string;
  name: string;
  maxPlayers: number;
  currentPlayers: number;
  status: 'waiting' | 'playing' | 'finished';
  createdAt: string;
  players: GamePlayer[];
}

export interface GamePlayer {
  id: string;
  nickname: string;
  isHost: boolean;
  isReady: boolean;
  score?: number;
}

export interface GameState {
  currentWord: string;
  wordChain: string[];
  currentTurn: string; // player id
  timeLeft: number;
  gameStatus: 'waiting' | 'playing' | 'paused' | 'finished';
  winner?: string;
}