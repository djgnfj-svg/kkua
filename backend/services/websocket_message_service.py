from typing import Dict, Any
from fastapi import WebSocket
from sqlalchemy.orm import Session

from repositories.gameroom_repository import GameroomRepository
from models.gameroom_model import ParticipantStatus
from models.guest_model import Guest
from ws_manager.connection_manager import ConnectionManager


class WebSocketMessageService:
    """웹소켓 메시지 처리 전담 서비스"""
    
    def __init__(self, db: Session, ws_manager: ConnectionManager):
        self.db = db
        self.ws_manager = ws_manager
        self.repository = GameroomRepository(db)

    async def handle_chat_message(
        self, 
        message_data: Dict[str, Any], 
        room_id: int, 
        guest: Guest
    ):
        """채팅 메시지 처리"""
        nickname = guest.nickname if guest.nickname else f"게스트_{guest.guest_id}"
        await self.ws_manager.broadcast_to_room(
            room_id,
            {
                "type": "chat",
                "guest_id": guest.guest_id,
                "nickname": nickname,
                "message": message_data.get("message", ""),
                "timestamp": message_data.get("timestamp", ""),
            },
        )

    async def handle_ready_toggle(
        self, 
        websocket: WebSocket, 
        room_id: int, 
        guest: Guest
    ):
        """준비 상태 토글 처리"""
        participant = self.repository.find_participant(room_id, guest.guest_id)
        if not participant:
            await self.ws_manager.send_personal_message(
                {
                    "type": "error",
                    "message": "준비 상태 변경 실패: 참가자 정보가 없습니다",
                },
                websocket,
            )
            return

        current_status = participant.status

        # 방장 확인 - 방장은 항상 준비 상태
        if participant.is_creator:
            await self.ws_manager.send_personal_message(
                {
                    "type": "ready_status_updated",
                    "is_ready": True,
                    "message": "방장은 항상 준비 상태입니다."
                },
                websocket,
            )
            return

        # 현재 상태에 따라 토글
        if current_status == ParticipantStatus.WAITING.value:
            new_status = ParticipantStatus.READY.value
            is_ready = True
        elif current_status == ParticipantStatus.READY.value:
            new_status = ParticipantStatus.WAITING.value
            is_ready = False
        else:
            # 게임 중에는 상태 변경 불가
            await self.ws_manager.send_personal_message(
                {
                    "type": "error",
                    "message": "게임 중에는 준비 상태를 변경할 수 없습니다",
                },
                websocket,
            )
            return

        # 참가자 상태 업데이트
        self.repository.update_participant_status(room_id, participant.participant_id, new_status)

        # 준비 상태 변경 알림
        await self.ws_manager.broadcast_ready_status(
            room_id, guest.guest_id, is_ready, guest.nickname
        )

        # 개인 메시지로 상태 변경 확인
        await self.ws_manager.send_personal_message(
            {"type": "ready_status_updated", "is_ready": is_ready}, websocket
        )

    async def handle_status_update(
        self, 
        message_data: Dict[str, Any], 
        websocket: WebSocket, 
        room_id: int, 
        guest: Guest
    ):
        """상태 업데이트 처리"""
        status = message_data.get("status", "WAITING")

        # 문자열을 열거형으로 변환
        try:
            status_enum = ParticipantStatus[status]
        except KeyError:
            await self.ws_manager.send_personal_message(
                {"type": "error", "message": f"유효하지 않은 상태 값: {status}"},
                websocket,
            )
            return

        # 참가자 상태 업데이트
        participant = self.repository.find_participant(room_id, guest.guest_id)
        if participant:
            updated = self.repository.update_participant_status(
                room_id, participant.participant_id, status_enum.value
            )

            # 상태 변경 알림
            status_value = (
                updated.status.value
                if hasattr(updated.status, "value")
                else updated.status
            )
            await self.ws_manager.broadcast_room_update(
                room_id,
                "status_changed",
                {
                    "guest_id": guest.guest_id,
                    "nickname": guest.nickname,
                    "status": status_value,
                },
            )
        else:
            await self.ws_manager.send_personal_message(
                {
                    "type": "error",
                    "message": "상태 업데이트 실패: 참가자 정보가 없습니다",
                },
                websocket,
            )

    async def handle_word_chain_message(
        self, 
        message_data: Dict[str, Any], 
        websocket: WebSocket, 
        room_id: int, 
        guest: Guest
    ):
        """끝말잇기 게임 메시지 처리"""
        action = message_data.get("action")

        if action == "initialize_game":
            await self._handle_initialize_game(websocket, room_id, guest)
        elif action == "start_game":
            await self._handle_start_game(message_data, websocket, room_id, guest)
        elif action == "submit_word":
            await self._handle_submit_word(message_data, websocket, room_id, guest)
        elif action == "end_game":
            await self._handle_end_game(websocket, room_id, guest)

    async def _handle_initialize_game(self, websocket: WebSocket, room_id: int, guest: Guest):
        """게임 초기화 처리"""
        room = self.repository.find_by_id(room_id)
        if room.created_by != guest.guest_id:
            await self.ws_manager.send_personal_message(
                {"type": "error", "message": "방장만 게임을 초기화할 수 있습니다."},
                websocket,
            )
            return

        # 참가자 목록 조회
        participants = self.repository.find_room_participants(room_id)
        participant_data = [
            {
                "guest_id": p.guest.guest_id,
                "nickname": p.guest.nickname,
                "status": p.status.value if hasattr(p.status, "value") else p.status,
                "is_creator": p.guest.guest_id == p.gameroom.created_by,
            }
            for p in participants
            if p.left_at is None
        ]

        # 게임 초기화
        self.ws_manager.initialize_word_chain_game(room_id, participant_data)

        # 초기화 알림
        await self.ws_manager.broadcast_room_update(
            room_id,
            "word_chain_initialized",
            {
                "message": "끝말잇기 게임이 초기화되었습니다.",
                "participants": participant_data,
            },
        )

    async def _handle_start_game(self, message_data: Dict[str, Any], websocket: WebSocket, room_id: int, guest: Guest):
        """게임 시작 처리"""
        # 방장 확인 - is_creator 필드 사용
        participant = self.repository.find_participant(room_id, guest.guest_id)
        if not participant or not participant.is_creator:
            await self.ws_manager.send_personal_message(
                {"type": "error", "message": "방장만 게임을 시작할 수 있습니다."},
                websocket,
            )
            return

        # 첫 단어 설정 (기본값 "끝말잇기")
        first_word = message_data.get("first_word", "끝말잇기")
        result = self.ws_manager.start_word_chain_game(room_id, first_word)

        if result:
            # 게임 시작 알림
            game_state = self.ws_manager.get_game_state(room_id)
            if game_state:
                await self.ws_manager.broadcast_room_update(
                    room_id,
                    "word_chain_started",
                    {
                        "message": "끝말잇기 게임이 시작되었습니다!",
                        "first_word": first_word,
                        "current_player_id": game_state["current_player_id"],
                        "current_player_nickname": game_state["nicknames"][
                            game_state["current_player_id"]
                        ],
                    },
                )

                # 게임 상태 전송
                await self.ws_manager.broadcast_word_chain_state(room_id)

                # 턴 타이머 시작
                await self.ws_manager.start_turn_timer(
                    room_id, game_state.get("time_limit", 15)
                )
        else:
            await self.ws_manager.send_personal_message(
                {"type": "error", "message": "게임 시작에 실패했습니다."}, websocket
            )

    async def _handle_submit_word(self, message_data: Dict[str, Any], websocket: WebSocket, room_id: int, guest: Guest):
        """단어 제출 처리"""
        word = message_data.get("word", "").strip()
        if not word:
            await self.ws_manager.send_personal_message(
                {"type": "error", "message": "단어를 입력해주세요."}, websocket
            )
            return

        # 단어 제출 처리
        result = self.ws_manager.submit_word(room_id, word, guest.guest_id)

        if result["success"]:
            # 단어 제출 성공 알림
            await self.ws_manager.broadcast_room_update(
                room_id,
                "word_chain_word_submitted",
                {
                    "word": word,
                    "submitted_by": {"id": guest.guest_id, "nickname": guest.nickname},
                    "next_player": result["next_player"],
                    "last_character": result["last_character"],
                },
            )

            # 게임 상태 전송
            await self.ws_manager.broadcast_word_chain_state(room_id)

            # 턴 타이머 시작
            game_state = self.ws_manager.get_game_state(room_id)
            if game_state:
                await self.ws_manager.start_turn_timer(
                    room_id, game_state.get("time_limit", 15)
                )
        else:
            # 단어 제출 실패 알림
            await self.ws_manager.send_personal_message(
                {"type": "word_chain_error", "message": result["message"]}, websocket
            )

    async def _handle_end_game(self, websocket: WebSocket, room_id: int, guest: Guest):
        """게임 종료 처리"""
        # 방장 확인 - is_creator 필드 사용
        participant = self.repository.find_participant(room_id, guest.guest_id)
        if not participant or not participant.is_creator:
            await self.ws_manager.send_personal_message(
                {"type": "error", "message": "방장만 게임을 종료할 수 있습니다."},
                websocket,
            )
            return

        # 게임 종료
        result = self.ws_manager.end_word_chain_game(room_id)

        if result:
            # 게임 종료 알림
            await self.ws_manager.broadcast_room_update(
                room_id,
                "word_chain_game_ended",
                {
                    "message": "게임이 종료되었습니다.",
                    "ended_by": {"id": guest.guest_id, "nickname": guest.nickname},
                },
            )
        else:
            await self.ws_manager.send_personal_message(
                {"type": "error", "message": "게임 종료에 실패했습니다."}, websocket
            )

    async def handle_host_change_notification(
        self, 
        room_id: int, 
        new_host_id: int, 
        new_host_nickname: str
    ):
        """방장 변경 알림 처리"""
        await self.ws_manager.broadcast_room_update(
            room_id,
            "host_changed",
            {
                "new_host_id": new_host_id,
                "new_host_nickname": new_host_nickname,
                "message": f"{new_host_nickname}님이 새로운 방장이 되었습니다.",
            },
        )

    async def handle_participant_list_update(self, room_id: int):
        """참가자 목록 업데이트 알림"""
        participants = self.repository.get_participants(room_id)
        
        await self.ws_manager.broadcast_room_update(
            room_id,
            "participant_list_updated",
            {
                "participants": participants,
                "message": "참가자 목록이 업데이트되었습니다.",
            },
        )

    def is_room_owner(self, room_id: int, guest_id: int) -> bool:
        """특정 게스트가 게임룸의 방장인지 확인합니다."""
        participant = self.repository.find_participant(room_id, guest_id)
        return participant is not None and participant.is_creator