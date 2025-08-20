"""
WebSocket 메시지 라우터
다양한 메시지 타입 처리 및 적절한 핸들러로 라우팅
"""

import asyncio
import logging
from typing import Dict, Any, Callable, Optional, List
from enum import Enum
from pydantic import BaseModel, ValidationError
from websocket.connection_manager import WebSocketManager, WebSocketConnection
from auth import AuthService

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket 메시지 타입"""
    # 연결 관리
    PING = "ping"
    PONG = "pong"
    
    # 룸 관리
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    ROOM_INFO = "room_info"
    
    # 게임 액션
    SUBMIT_WORD = "submit_word"
    USE_ITEM = "use_item"
    READY_GAME = "ready_game"
    START_GAME = "start_game"
    
    # 채팅
    CHAT_MESSAGE = "chat_message"
    
    # 시스템
    ERROR = "error"
    SUCCESS = "success"
    NOTIFICATION = "notification"


class BaseMessage(BaseModel):
    """기본 메시지 구조"""
    type: MessageType
    data: Dict[str, Any] = {}
    timestamp: Optional[str] = None
    request_id: Optional[str] = None


class MessageRouter:
    """WebSocket 메시지 라우터"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.auth_service = AuthService()
        
        # 메시지 핸들러 등록
        self.handlers: Dict[MessageType, Callable] = {}
        self._register_handlers()
        
        # 권한이 필요한 액션들
        self.auth_required_actions = {
            MessageType.SUBMIT_WORD,
            MessageType.USE_ITEM,
            MessageType.READY_GAME,
            MessageType.START_GAME,
            MessageType.CHAT_MESSAGE
        }
    
    def _register_handlers(self):
        """핸들러 등록"""
        self.handlers.update({
            MessageType.PING: self._handle_ping,
            MessageType.JOIN_ROOM: self._handle_join_room,
            MessageType.LEAVE_ROOM: self._handle_leave_room,
            MessageType.ROOM_INFO: self._handle_room_info,
            MessageType.SUBMIT_WORD: self._handle_submit_word,
            MessageType.USE_ITEM: self._handle_use_item,
            MessageType.READY_GAME: self._handle_ready_game,
            MessageType.START_GAME: self._handle_start_game,
            MessageType.CHAT_MESSAGE: self._handle_chat_message,
        })
    
    def add_handler(self, message_type: MessageType, handler: Callable):
        """외부 핸들러 추가"""
        self.handlers[message_type] = handler
        logger.info(f"핸들러 등록: {message_type}")
    
    async def route_message(self, connection: WebSocketConnection, raw_message: Dict[str, Any]) -> bool:
        """메시지 라우팅"""
        try:
            # 메시지 검증
            message = BaseMessage(**raw_message)
            
            # 핸들러 찾기
            handler = self.handlers.get(message.type)
            if not handler:
                await self._send_error(connection, f"지원하지 않는 메시지 타입: {message.type}")
                return False
            
            # 권한 확인
            if message.type in self.auth_required_actions:
                if not await self._check_permissions(connection, message.type):
                    await self._send_error(connection, "권한이 없습니다")
                    return False
            
            # 핸들러 실행
            result = await handler(connection, message)
            
            # 성공 응답 (요청 ID가 있는 경우)
            if result and message.request_id:
                await connection.send_json({
                    "type": MessageType.SUCCESS,
                    "data": {"message": "처리 완료"},
                    "request_id": message.request_id
                })
            
            return result
            
        except ValidationError as e:
            logger.warning(f"메시지 검증 실패 (user_id={connection.user_id}): {e}")
            await self._send_error(connection, "올바르지 않은 메시지 형식입니다")
            return False
        except Exception as e:
            logger.error(f"메시지 라우팅 중 오류 (user_id={connection.user_id}): {e}")
            await self._send_error(connection, "메시지 처리 중 오류가 발생했습니다")
            return False
    
    async def _check_permissions(self, connection: WebSocketConnection, action: MessageType) -> bool:
        """권한 확인"""
        try:
            # JWT 토큰에서 사용자 정보를 이미 검증했으므로 기본 권한 확인
            user_info = {
                "user_id": connection.user_id,
                "nickname": connection.nickname,
                "permissions": ["game_play", "chat"]  # 기본 게스트 권한
            }
            
            return self.auth_service.validate_game_permission(user_info, action.value)
            
        except Exception as e:
            logger.error(f"권한 확인 중 오류 (user_id={connection.user_id}): {e}")
            return False
    
    async def _send_error(self, connection: WebSocketConnection, message: str, request_id: Optional[str] = None):
        """에러 메시지 전송"""
        error_data = {
            "type": MessageType.ERROR,
            "data": {"error": message},
        }
        
        if request_id:
            error_data["request_id"] = request_id
        
        await connection.send_json(error_data)
    
    # === 핸들러 메서드들 ===
    
    async def _handle_ping(self, connection: WebSocketConnection, message: BaseMessage) -> bool:
        """핑 처리"""
        connection.update_ping()
        await connection.send_json({
            "type": MessageType.PONG,
            "data": {"timestamp": message.data.get("timestamp")},
            "request_id": message.request_id
        })
        return True
    
    async def _handle_join_room(self, connection: WebSocketConnection, message: BaseMessage) -> bool:
        """룸 참가 처리"""
        room_id = message.data.get("room_id")
        if not room_id:
            await self._send_error(connection, "room_id가 필요합니다", message.request_id)
            return False
        
        success = await self.websocket_manager.join_room(connection.user_id, room_id)
        
        if success:
            # 룸 정보 전송
            room_users = self.websocket_manager.get_room_users(room_id)
            await connection.send_json({
                "type": "room_joined",
                "data": {
                    "room_id": room_id,
                    "users": room_users,
                    "user_count": len(room_users)
                },
                "request_id": message.request_id
            })
        else:
            await self._send_error(connection, "룸 참가에 실패했습니다", message.request_id)
        
        return success
    
    async def _handle_leave_room(self, connection: WebSocketConnection, message: BaseMessage) -> bool:
        """룸 나가기 처리"""
        success = await self.websocket_manager.leave_room(connection.user_id)
        
        if success:
            await connection.send_json({
                "type": "room_left",
                "data": {"message": "룸에서 나갔습니다"},
                "request_id": message.request_id
            })
        else:
            await self._send_error(connection, "룸 나가기에 실패했습니다", message.request_id)
        
        return success
    
    async def _handle_room_info(self, connection: WebSocketConnection, message: BaseMessage) -> bool:
        """룸 정보 조회"""
        if not connection.room_id:
            await self._send_error(connection, "룸에 참가하지 않았습니다", message.request_id)
            return False
        
        room_users = self.websocket_manager.get_room_users(connection.room_id)
        await connection.send_json({
            "type": "room_info",
            "data": {
                "room_id": connection.room_id,
                "users": room_users,
                "user_count": len(room_users)
            },
            "request_id": message.request_id
        })
        return True
    
    async def _handle_submit_word(self, connection: WebSocketConnection, message: BaseMessage) -> bool:
        """단어 제출 처리"""
        if not connection.room_id:
            await self._send_error(connection, "게임 룸에 참가해야 합니다", message.request_id)
            return False
        
        word = message.data.get("word")
        if not word:
            await self._send_error(connection, "단어가 필요합니다", message.request_id)
            return False
        
        # 게임 핸들러로 위임 (Phase 3에서 구현)
        logger.info(f"단어 제출 요청: user_id={connection.user_id}, word={word}, room_id={connection.room_id}")
        
        # 임시 응답 (Phase 3에서 실제 게임 로직 구현)
        await self.websocket_manager.broadcast_to_room(connection.room_id, {
            "type": "word_submitted",
            "data": {
                "user_id": connection.user_id,
                "nickname": connection.nickname,
                "word": word,
                "status": "pending_validation"
            }
        })
        
        return True
    
    async def _handle_use_item(self, connection: WebSocketConnection, message: BaseMessage) -> bool:
        """아이템 사용 처리"""
        if not connection.room_id:
            await self._send_error(connection, "게임 룸에 참가해야 합니다", message.request_id)
            return False
        
        item_id = message.data.get("item_id")
        target_user_id = message.data.get("target_user_id")
        
        if not item_id:
            await self._send_error(connection, "아이템 ID가 필요합니다", message.request_id)
            return False
        
        # 게임 핸들러로 위임 (Phase 3에서 구현)
        logger.info(f"아이템 사용 요청: user_id={connection.user_id}, item_id={item_id}, target={target_user_id}")
        
        # 임시 응답
        await self.websocket_manager.broadcast_to_room(connection.room_id, {
            "type": "item_used",
            "data": {
                "user_id": connection.user_id,
                "nickname": connection.nickname,
                "item_id": item_id,
                "target_user_id": target_user_id,
                "status": "pending_execution"
            }
        })
        
        return True
    
    async def _handle_ready_game(self, connection: WebSocketConnection, message: BaseMessage) -> bool:
        """게임 준비 처리"""
        if not connection.room_id:
            await self._send_error(connection, "게임 룸에 참가해야 합니다", message.request_id)
            return False
        
        ready_status = message.data.get("ready", True)
        
        logger.info(f"게임 준비 상태 변경: user_id={connection.user_id}, ready={ready_status}")
        
        await self.websocket_manager.broadcast_to_room(connection.room_id, {
            "type": "player_ready_status",
            "data": {
                "user_id": connection.user_id,
                "nickname": connection.nickname,
                "ready": ready_status
            }
        })
        
        return True
    
    async def _handle_start_game(self, connection: WebSocketConnection, message: BaseMessage) -> bool:
        """게임 시작 처리"""
        if not connection.room_id:
            await self._send_error(connection, "게임 룸에 참가해야 합니다", message.request_id)
            return False
        
        logger.info(f"게임 시작 요청: user_id={connection.user_id}, room_id={connection.room_id}")
        
        # 게임 핸들러로 위임 (Phase 3에서 구현)
        await self.websocket_manager.broadcast_to_room(connection.room_id, {
            "type": "game_start_requested",
            "data": {
                "requested_by": connection.user_id,
                "nickname": connection.nickname
            }
        })
        
        return True
    
    async def _handle_chat_message(self, connection: WebSocketConnection, message: BaseMessage) -> bool:
        """채팅 메시지 처리"""
        if not connection.room_id:
            await self._send_error(connection, "룸에 참가해야 합니다", message.request_id)
            return False
        
        chat_message = message.data.get("message")
        if not chat_message:
            await self._send_error(connection, "메시지 내용이 필요합니다", message.request_id)
            return False
        
        # 메시지 길이 제한
        if len(chat_message) > 500:
            await self._send_error(connection, "메시지가 너무 깁니다 (최대 500자)", message.request_id)
            return False
        
        # 룸의 모든 사용자에게 브로드캐스트
        await self.websocket_manager.broadcast_to_room(connection.room_id, {
            "type": "chat_message",
            "data": {
                "user_id": connection.user_id,
                "nickname": connection.nickname,
                "message": chat_message,
                "timestamp": message.timestamp
            }
        })
        
        return True
    
    def get_handler_stats(self) -> Dict[str, Any]:
        """핸들러 통계"""
        return {
            "registered_handlers": len(self.handlers),
            "handler_types": list(self.handlers.keys()),
            "auth_required_actions": list(self.auth_required_actions)
        }