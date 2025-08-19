"""
Word chain game engine for real-time gameplay
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class WordChainGameEngine:
    """끝말잇기 게임의 실시간 로직을 관리하는 엔진"""

    def __init__(self, websocket_manager, db: Optional[Session] = None):
        self.websocket_manager = websocket_manager
        self.db = db
        # 게임 상태 저장: {room_id: game_state}
        self.games: Dict[int, Dict[str, Any]] = {}
        # 턴 타이머 관리: {room_id: timer_task}
        self.timers: Dict[int, asyncio.Task] = {}

    def initialize_word_chain_game(
        self, room_id: int, participants: List[Dict], max_rounds: int = 10
    ) -> Dict[str, Any]:
        """끝말잇기 게임을 초기화합니다"""
        game_state = {
            "room_id": room_id,
            "status": "initialized",
            "participants": participants,
            "current_turn": 0,
            "current_player_idx": 0,
            "word_chain": [],
            "used_words": set(),
            "max_rounds": max_rounds,
            "current_round": 0,
            "scores": {p["guest_id"]: 0 for p in participants},
            "turn_start_time": None,
            "time_limit": 15,
            "game_start_time": datetime.utcnow(),
            "last_word": None,
            "eliminated_players": set(),
        }

        self.games[room_id] = game_state

        return game_state

    def get_game_state(self, room_id: int) -> Dict[str, Any]:
        """현재 게임 상태를 반환합니다"""
        return self.games.get(room_id, {})

    def start_word_chain_game(
        self, room_id: int, first_word: str = "끝말잇기"
    ) -> Dict[str, Any]:
        """끝말잇기 게임을 시작합니다"""
        if room_id not in self.games:
            return {"error": "Game not initialized"}

        game = self.games[room_id]
        game["status"] = "playing"
        game["last_word"] = first_word
        game["word_chain"] = [
            {
                "word": first_word,
                "guest_id": None,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ]
        game["used_words"].add(first_word)
        game["turn_start_time"] = datetime.utcnow()

        return game

    def validate_word(self, room_id: int, word: str, guest_id: int) -> bool:
        """제출된 단어의 유효성을 검사합니다"""
        if room_id not in self.games:
            return False

        game = self.games[room_id]

        # 기본 검증
        if not word or len(word.strip()) < 2:
            return False

        word = word.strip()

        # 이미 사용된 단어인지 확인
        if word in game["used_words"]:
            return False

        # 끝말잇기 규칙 확인
        if game["last_word"]:
            last_char = game["last_word"][-1]
            first_char = word[0]
            if last_char != first_char:
                return False

        # 현재 플레이어 턴인지 확인
        current_player = game["participants"][game["current_player_idx"]]
        if current_player["guest_id"] != guest_id:
            return False

        return True

    def submit_word(self, room_id: int, word: str, guest_id: int) -> Dict[str, Any]:
        """단어를 제출하고 처리합니다"""
        if not self.validate_word(room_id, word, guest_id):
            return {"valid": False, "error": "Invalid word"}

        game = self.games[room_id]
        word = word.strip()

        # 단어 추가
        game["word_chain"].append(
            {
                "word": word,
                "guest_id": guest_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        game["used_words"].add(word)
        game["last_word"] = word

        # 점수 추가
        base_score = len(word) * 10
        game["scores"][guest_id] += base_score

        # 다음 플레이어로 턴 변경
        game["current_player_idx"] = (game["current_player_idx"] + 1) % len(
            game["participants"]
        )
        game["turn_start_time"] = datetime.utcnow()
        game["current_turn"] += 1

        # 게임 종료 조건 확인
        if game["current_turn"] >= game["max_rounds"] * len(game["participants"]):
            return self.end_word_chain_game(room_id)

        return {
            "valid": True,
            "word": word,
            "score": base_score,
            "next_player": game["participants"][game["current_player_idx"]],
            "game_state": game,
        }

    async def start_turn_timer(self, room_id: int, time_limit: int = 15):
        """턴 타이머를 시작합니다"""
        # 기존 타이머 취소
        if room_id in self.timers:
            self.timers[room_id].cancel()

        async def timer_callback():
            try:
                await asyncio.sleep(time_limit)
                await self._handle_turn_timeout(room_id)
            except asyncio.CancelledError:
                pass

        self.timers[room_id] = asyncio.create_task(timer_callback())

    async def _handle_turn_timeout(self, room_id: int):
        """턴 타임아웃 처리"""
        if room_id not in self.games:
            return

        game = self.games[room_id]
        current_player = game["participants"][game["current_player_idx"]]

        # 플레이어를 게임에서 제거하지 않고 턴만 넘김
        game["current_player_idx"] = (game["current_player_idx"] + 1) % len(
            game["participants"]
        )
        game["turn_start_time"] = datetime.utcnow()

        await self.websocket_manager.broadcast_to_room(
            room_id,
            {
                "type": "turn_timeout",
                "timed_out_player": current_player,
                "next_player": game["participants"][game["current_player_idx"]],
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def broadcast_word_chain_state(self, room_id: int):
        """현재 게임 상태를 브로드캐스트합니다"""
        if room_id not in self.games:
            return

        game = self.games[room_id]

        message = {
            "type": "game_state_update",
            "game_state": {
                "status": game["status"],
                "current_turn": game["current_turn"],
                "current_player": game["participants"][game["current_player_idx"]],
                "last_word": game["last_word"],
                "scores": game["scores"],
                "word_count": len(game["word_chain"]),
                "turn_start_time": game["turn_start_time"].isoformat()
                if game["turn_start_time"]
                else None,
                "time_limit": game["time_limit"],
            },
        }

        await self.websocket_manager.broadcast_to_room(room_id, message)

    def end_word_chain_game(self, room_id: int) -> Dict[str, Any]:
        """끝말잇기 게임을 종료합니다"""
        if room_id not in self.games:
            return {"error": "Game not found"}

        game = self.games[room_id]
        game["status"] = "completed"
        game["end_time"] = datetime.utcnow()

        # 승자 결정
        winner_id = max(game["scores"], key=game["scores"].get)
        winner = next(
            (p for p in game["participants"] if p["guest_id"] == winner_id), None
        )

        # 타이머 정리
        if room_id in self.timers:
            self.timers[room_id].cancel()
            del self.timers[room_id]

        result = {
            "status": "completed",
            "winner": winner,
            "final_scores": game["scores"],
            "total_words": len(game["word_chain"]),
            "total_turns": game["current_turn"],
            "game_duration": (
                game["end_time"] - game["game_start_time"]
            ).total_seconds(),
        }

        # 게임 상태 정리
        del self.games[room_id]

        return result
