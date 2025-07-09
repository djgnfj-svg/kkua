from typing import Dict, List
import asyncio
from datetime import datetime

from .websocket_manager import WebSocketManager


class WordChainGameManager:
    """끝말잇기 게임 전담 매니저"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        
        # 끝말잇기 게임 상태 관리
        self.word_chain_games: Dict[int, Dict] = {}  # room_id: 게임 상태
        self.turn_timers: Dict[int, asyncio.Task] = {}  # room_id: 타이머 태스크

    def initialize_word_chain_game(self, room_id: int, participants: List[Dict]):
        """끝말잇기 게임 초기화"""
        # 참가자 ID 목록
        participant_ids = [p["guest_id"] for p in participants]
        participant_nicknames = {p["guest_id"]: p["nickname"] for p in participants}

        # 게임 상태 초기화
        self.word_chain_games[room_id] = {
            "participants": participant_ids,
            "nicknames": participant_nicknames,
            "current_player_index": 0,
            "current_player_id": participant_ids[0],
            "current_word": "",
            "last_character": "",
            "used_words": [],
            "turn_number": 0,
            "game_started": False,
            "time_limit": 15,  # 기본 15초
            "is_game_over": False,
        }
        print(f"끝말잇기 게임 초기화: room_id={room_id}, 참가자 수={len(participant_ids)}")

    def get_game_state(self, room_id: int) -> Dict:
        """현재 게임 상태 반환"""
        if room_id not in self.word_chain_games:
            return None
        return self.word_chain_games[room_id]

    def start_word_chain_game(self, room_id: int, first_word: str = "끝말잇기"):
        """게임 시작"""
        if room_id not in self.word_chain_games:
            return False

        game_state = self.word_chain_games[room_id]
        game_state["current_word"] = first_word
        game_state["last_character"] = first_word[-1]
        game_state["game_started"] = True
        game_state["turn_number"] = 1
        game_state["used_words"] = [first_word]

        # 첫 플레이어 설정
        game_state["current_player_index"] = 0
        game_state["current_player_id"] = game_state["participants"][0]

        print(f"끝말잇기 게임 시작: room_id={room_id}, 첫 단어={first_word}")
        return True

    def validate_word(self, room_id: int, word: str, guest_id: int) -> bool:
        """단어 유효성 검사"""
        if room_id not in self.word_chain_games:
            return False

        game_state = self.word_chain_games[room_id]

        # 현재 플레이어 확인
        if game_state["current_player_id"] != guest_id:
            print(f"차례가 아닌 플레이어의 단어 제출: {guest_id}")
            return False

        # 이미 사용된 단어인지 확인
        if word in game_state["used_words"]:
            print(f"이미 사용된 단어: {word}")
            return False

        # 첫 글자가 이전 단어의 마지막 글자인지 확인
        if not word.startswith(game_state["last_character"]):
            print(f"이전 단어의 마지막 글자로 시작하지 않음: {word}")
            return False

        # 한글 단어인지 확인 (간단한 검증)
        if not all("\uac00" <= char <= "\ud7a3" for char in word):
            print(f"유효한 한글 단어가 아님: {word}")
            return False

        return True

    def submit_word(self, room_id: int, word: str, guest_id: int) -> Dict:
        """단어 제출 처리"""
        if room_id not in self.word_chain_games:
            return {"success": False, "message": "게임이 초기화되지 않았습니다."}

        game_state = self.word_chain_games[room_id]

        # 게임이 시작되었는지 확인
        if not game_state["game_started"]:
            return {"success": False, "message": "게임이 아직 시작되지 않았습니다."}

        # 게임이 끝났는지 확인
        if game_state["is_game_over"]:
            return {"success": False, "message": "게임이 이미 종료되었습니다."}

        # 단어 유효성 검사
        is_valid = self.validate_word(room_id, word, guest_id)
        if not is_valid:
            return {"success": False, "message": "유효하지 않은 단어입니다."}

        # 타이머 취소
        if room_id in self.turn_timers:
            self.turn_timers[room_id].cancel()

        # 단어 등록
        game_state["current_word"] = word
        game_state["last_character"] = word[-1]
        game_state["used_words"].append(word)
        game_state["turn_number"] += 1

        # 다음 플레이어로 턴 넘기기
        game_state["current_player_index"] = (
            game_state["current_player_index"] + 1
        ) % len(game_state["participants"])
        game_state["current_player_id"] = game_state["participants"][
            game_state["current_player_index"]
        ]

        print(f"단어 제출 성공: room_id={room_id}, 단어={word}, 다음 플레이어={game_state['current_player_id']}")

        return {
            "success": True,
            "message": "단어가 성공적으로 제출되었습니다.",
            "word": word,
            "next_player": {
                "id": game_state["current_player_id"],
                "nickname": game_state["nicknames"][game_state["current_player_id"]],
            },
            "last_character": game_state["last_character"],
        }

    async def start_turn_timer(self, room_id: int, time_limit: int = 15):
        """턴 타이머 시작"""
        if room_id not in self.word_chain_games:
            return

        # 기존 타이머 취소
        if room_id in self.turn_timers:
            self.turn_timers[room_id].cancel()

        # 타이머 시작
        self.turn_timers[room_id] = asyncio.create_task(
            self._run_timer(room_id, time_limit)
        )

    async def _run_timer(self, room_id: int, time_limit: int):
        """타이머 실행 함수"""
        try:
            game_state = self.word_chain_games.get(room_id)
            if not game_state:
                return

            # 카운트다운 전송
            for i in range(time_limit, 0, -1):
                if (
                    room_id not in self.word_chain_games
                    or not game_state["game_started"]
                ):
                    return

                # 남은 시간 업데이트
                await self.websocket_manager.broadcast_room_update(
                    room_id,
                    "word_chain_timer",
                    {
                        "remaining_time": i,
                        "current_player_id": game_state["current_player_id"],
                        "current_player_nickname": game_state["nicknames"][
                            game_state["current_player_id"]
                        ],
                    },
                )

                await asyncio.sleep(1)

            # 제한 시간 초과
            if room_id in self.word_chain_games and game_state["game_started"]:
                # 현재 플레이어 패배 처리
                loser_id = game_state["current_player_id"]
                loser_nickname = game_state["nicknames"][loser_id]

                # 게임 종료
                game_state["is_game_over"] = True

                # 게임 종료 메시지 전송
                await self.websocket_manager.broadcast_room_update(
                    room_id,
                    "word_chain_game_over",
                    {
                        "reason": "time_out",
                        "loser_id": loser_id,
                        "loser_nickname": loser_nickname,
                        "message": f"{loser_nickname}님이 제한 시간 내에 단어를 제출하지 못했습니다.",
                    },
                )

        except asyncio.CancelledError:
            # 타이머가 취소됨 (정상)
            pass
        except Exception as e:
            print(f"타이머 오류: {str(e)}")

    async def broadcast_word_chain_state(self, room_id: int):
        """현재 끝말잇기 게임 상태 브로드캐스트"""
        if room_id not in self.word_chain_games:
            return

        game_state = self.word_chain_games[room_id]

        await self.websocket_manager.broadcast_room_update(
            room_id,
            "word_chain_state",
            {
                "current_word": game_state["current_word"],
                "current_player_id": game_state["current_player_id"],
                "current_player_nickname": game_state["nicknames"][
                    game_state["current_player_id"]
                ],
                "last_character": game_state["last_character"],
                "used_words": game_state["used_words"],
                "turn_number": game_state["turn_number"],
                "is_game_over": game_state["is_game_over"],
            },
        )

    def end_word_chain_game(self, room_id: int):
        """끝말잇기 게임 종료"""
        if room_id in self.word_chain_games:
            # 게임 상태 정리
            if room_id in self.turn_timers:
                self.turn_timers[room_id].cancel()
                del self.turn_timers[room_id]

            del self.word_chain_games[room_id]
            print(f"끝말잇기 게임 종료: room_id={room_id}")
            return True
        return False