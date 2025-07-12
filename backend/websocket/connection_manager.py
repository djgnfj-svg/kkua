from typing import Dict, List, Optional
from fastapi import WebSocket
from datetime import datetime
from sqlalchemy.orm import Session

from .websocket_manager import WebSocketConnectionManager
from .word_chain_manager import WordChainGameEngine


class GameRoomWebSocketFacade:
    """게임방 WebSocket 기능의 통합 인터페이스
    
    WebSocket 연결 관리와 게임 로직을 통합하여 
    상위 레벨에서 사용하기 쉬운 단일 인터페이스를 제공합니다.
    """
    
    def __init__(self, db: Optional[Session] = None):
        self.websocket_manager = WebSocketConnectionManager()
        self.word_chain_engine = WordChainGameEngine(self.websocket_manager, db)

    # ============ WebSocket 연결 관리 ============
    
    async def connect(self, websocket: WebSocket, room_id: int, guest_id: int):
        """웹소켓 연결을 관리합니다."""
        await self.websocket_manager.connect(websocket, room_id, guest_id)
        await self.broadcast_room_update(room_id, "user_joined", {"guest_id": guest_id})

    async def disconnect(self, websocket: WebSocket, room_id: int, guest_id: int):
        """웹소켓 연결 제거"""
        await self.websocket_manager.disconnect(websocket, room_id, guest_id)
        await self.broadcast_to_room(
            room_id,
            {
                "type": "user_left",
                "guest_id": guest_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """특정 웹소켓에 메시지 전송"""
        await self.websocket_manager.send_personal_message(message, websocket)

    async def broadcast_to_room(self, room_id: int, message: dict):
        """방의 모든 사용자에게 메시지 전송"""
        await self.websocket_manager.broadcast_to_room(room_id, message)

    async def broadcast_room_update(self, room_id: int, update_type: str, data: dict = None):
        """방 상태 업데이트 알림"""
        await self.websocket_manager.broadcast_room_update(room_id, update_type, data)

    async def broadcast_ready_status(self, room_id: int, guest_id: int, is_ready: bool, nickname: str = None):
        """게스트의 준비 상태 변경을 브로드캐스트합니다."""
        message = {
            "type": "ready_status_changed",
            "guest_id": guest_id,
            "nickname": nickname,
            "is_ready": is_ready,
        }
        await self.websocket_manager.broadcast_room_update(room_id, "ready_status_changed", message)

    # ============ 끝말잇기 게임 관리 ============
    
    def initialize_word_chain_game(self, room_id: int, participants: List[Dict], max_rounds: int = 10):
        """끝말잇기 게임 초기화"""
        return self.word_chain_engine.initialize_word_chain_game(room_id, participants, max_rounds)

    def get_game_state(self, room_id: int) -> Dict:
        """현재 게임 상태 반환"""
        return self.word_chain_engine.get_game_state(room_id)

    def start_word_chain_game(self, room_id: int, first_word: str = "끝말잇기"):
        """게임 시작"""
        return self.word_chain_engine.start_word_chain_game(room_id, first_word)

    def validate_word(self, room_id: int, word: str, guest_id: int) -> bool:
        """단어 유효성 검사"""
        return self.word_chain_engine.validate_word(room_id, word, guest_id)

    def submit_word(self, room_id: int, word: str, guest_id: int) -> Dict:
        """단어 제출 처리"""
        return self.word_chain_engine.submit_word(room_id, word, guest_id)

    async def start_turn_timer(self, room_id: int, time_limit: int = 15):
        """턴 타이머 시작"""
        await self.word_chain_engine.start_turn_timer(room_id, time_limit)

    async def broadcast_word_chain_state(self, room_id: int):
        """현재 끝말잇기 게임 상태 브로드캐스트"""
        await self.word_chain_engine.broadcast_word_chain_state(room_id)

    def end_word_chain_game(self, room_id: int):
        """끝말잇기 게임 종료"""
        return self.word_chain_engine.end_word_chain_game(room_id)

    # ============ 편의 메서드 ============
    
    def get_user_connection(self, guest_id: int):
        """특정 사용자의 연결 정보 조회"""
        return None