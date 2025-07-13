from typing import Dict, Any
from fastapi import WebSocket, HTTPException
from sqlalchemy.orm import Session
from pydantic import ValidationError
import logging
import time
from datetime import datetime

from repositories.gameroom_repository import GameroomRepository
from models.gameroom_model import ParticipantStatus
from models.guest_model import Guest
from websocket.connection_manager import GameRoomWebSocketFacade
from schemas.websocket_schema import validate_websocket_message, MessageType, GameActionType

logger = logging.getLogger(__name__)


class WebSocketMessageService:
    """웹소켓 메시지 처리 전담 서비스"""
    
    def __init__(self, db: Session, ws_manager: GameRoomWebSocketFacade):
        self.db = db
        self.ws_manager = ws_manager
        self.repository = GameroomRepository(db)
    
    async def validate_and_process_message(
        self, 
        message_data: Dict[str, Any], 
        room_id: int, 
        guest: Guest,
        websocket: WebSocket
    ) -> bool:
        """메시지 검증 및 처리"""
        try:
            # 메시지 검증
            validated_message = validate_websocket_message(message_data)
            
            # 타입별 처리
            if validated_message.type == MessageType.CHAT:
                await self.handle_chat_message(validated_message.dict(), room_id, guest)
            elif validated_message.type == MessageType.GAME_ACTION:
                await self.handle_game_action(validated_message.dict(), room_id, guest, websocket)
            elif validated_message.type == MessageType.WORD_CHAIN:
                await self.handle_word_chain(validated_message.dict(), room_id, guest, websocket)
            elif validated_message.type == MessageType.PING:
                await self.handle_ping(websocket)
            else:
                logger.warning(f"처리되지 않은 메시지 타입: {validated_message.type}")
                return False
            
            return True
            
        except ValidationError as e:
            logger.warning(f"메시지 검증 실패: {e}")
            await self.send_error_message(websocket, f"잘못된 메시지 형식: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"메시지 처리 중 오류: {e}")
            await self.send_error_message(websocket, "메시지 처리 중 오류가 발생했습니다")
            return False
    
    async def send_error_message(self, websocket: WebSocket, error_message: str):
        """에러 메시지 전송"""
        try:
            await self.ws_manager.send_personal_message(
                {
                    "type": "error",
                    "message": error_message,
                    "timestamp": str(datetime.utcnow())
                },
                websocket
            )
        except Exception as e:
            logger.error(f"에러 메시지 전송 실패: {e}")
    
    async def handle_ping(self, websocket: WebSocket):
        """Ping 메시지 처리 - Pong 응답"""
        try:
            await self.ws_manager.send_personal_message(
                {
                    "type": "pong",
                    "timestamp": time.time()
                },
                websocket
            )
        except Exception as e:
            logger.error(f"Pong 응답 실패: {e}")
    
    async def handle_game_action(
        self, 
        message_data: Dict[str, Any], 
        room_id: int, 
        guest: Guest,
        websocket: WebSocket
    ):
        """게임 액션 처리"""
        action = message_data.get('action')
        
        if action == GameActionType.TOGGLE_READY:
            await self.handle_ready_toggle(websocket, room_id, guest)
        elif action == GameActionType.START_GAME:
            await self.handle_start_game(websocket, room_id, guest)
        elif action == GameActionType.END_GAME:
            await self.handle_end_game(websocket, room_id, guest)
        else:
            await self.send_error_message(websocket, f"지원되지 않는 게임 액션: {action}")
    
    async def handle_word_chain(
        self, 
        message_data: Dict[str, Any], 
        room_id: int, 
        guest: Guest,
        websocket: WebSocket
    ):
        """끝말잇기 단어 처리"""
        word = message_data.get('word')
        
        # WordChainGameEngine을 통한 처리
        if hasattr(self.ws_manager, 'word_chain_engine'):
            try:
                result = await self.ws_manager.word_chain_engine.handle_word_submission(
                    room_id, guest.guest_id, word
                )
                
                # 결과를 방 전체에 브로드캐스트
                await self.ws_manager.broadcast_to_room(room_id, {
                    "type": "word_chain_result",
                    "guest_id": guest.guest_id,
                    "word": word,
                    "result": result,
                    "timestamp": message_data.get('timestamp')
                })
                
            except Exception as e:
                logger.error(f"단어 처리 중 오류: {e}")
                await self.send_error_message(websocket, "단어 처리 중 오류가 발생했습니다")

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
        print(f"🔄 준비 상태 토글 요청: room_id={room_id}, guest_id={guest.guest_id}")
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

    async def handle_start_game(
        self, 
        websocket: WebSocket, 
        room_id: int, 
        guest: Guest
    ):
        """게임 시작 처리"""
        try:
            # GameroomService를 통해 게임 시작
            from services.gameroom_service import GameroomService
            gameroom_service = GameroomService(self.db)
            
            result = await gameroom_service.start_game(room_id, guest)
            
            # 성공 응답 전송
            await self.ws_manager.send_personal_message(
                {
                    "type": "game_start_success",
                    "message": result.get("message", "게임이 시작되었습니다!"),
                    "status": result.get("status", "PLAYING")
                },
                websocket
            )
            
        except HTTPException as e:
            await self.send_error_message(websocket, e.detail)
        except Exception as e:
            logger.error(f"게임 시작 중 오류: {e}")
            await self.send_error_message(websocket, "게임 시작 중 오류가 발생했습니다")
    
    async def handle_end_game(
        self, 
        websocket: WebSocket, 
        room_id: int, 
        guest: Guest
    ):
        """게임 종료 처리"""
        try:
            # GameroomService를 통해 게임 종료
            from services.gameroom_service import GameroomService
            gameroom_service = GameroomService(self.db)
            
            result = gameroom_service.end_game(room_id, guest)
            
            # 성공 응답 전송
            await self.ws_manager.send_personal_message(
                {
                    "type": "game_end_success",
                    "message": result.get("message", "게임이 종료되었습니다!"),
                    "status": result.get("status", "FINISHED")
                },
                websocket
            )
            
        except HTTPException as e:
            await self.send_error_message(websocket, e.detail)
        except Exception as e:
            logger.error(f"게임 종료 중 오류: {e}")
            await self.send_error_message(websocket, "게임 종료 중 오류가 발생했습니다")

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

        # 게임 초기화 - max_rounds 정보 가져오기
        room = self.repository.find_by_id(room_id)
        max_rounds = room.max_rounds if room else 10
        self.ws_manager.initialize_word_chain_game(room_id, participant_data, max_rounds)

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
            # 게임 종료 체크
            if result.get("game_over"):
                # 게임 종료 처리
                await self.ws_manager.broadcast_room_update(
                    room_id,
                    "word_chain_game_over",
                    {
                        "reason": result.get("game_over_reason"),
                        "message": f"게임이 종료되었습니다! (라운드 {result['max_rounds']} 완료)",
                        "final_word": word,
                        "submitted_by": {"id": guest.guest_id, "nickname": guest.nickname},
                    },
                )
                
                # 게임 상태를 DB에서도 종료로 변경
                from services.game_state_service import GameStateService
                game_state_service = GameStateService(self.db)
                game_state_service.end_game(room_id)
                
                # 게임 종료 WebSocket 메시지 전송 (결과 페이지로 이동)
                await self.ws_manager.broadcast_room_update(
                    room_id,
                    "game_ended",
                    {
                        "room_id": room_id,
                        "message": "게임이 종료되었습니다. 결과 페이지로 이동합니다.",
                    },
                )
            else:
                # 단어 제출 성공 알림
                await self.ws_manager.broadcast_room_update(
                    room_id,
                    "word_chain_word_submitted",
                    {
                        "word": word,
                        "submitted_by": {"id": guest.guest_id, "nickname": guest.nickname},
                        "next_player": result["next_player"],
                        "last_character": result["last_character"],
                        "current_round": result["current_round"],
                        "max_rounds": result["max_rounds"],
                    },
                )

                # 게임 상태 전송
                await self.ws_manager.broadcast_word_chain_state(room_id)

                # 턴 타이머 시작
                game_state = self.ws_manager.get_game_state(room_id)
                if game_state and not game_state.get("is_game_over"):
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