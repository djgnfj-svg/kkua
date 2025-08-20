"""
WebSocket 엔드포인트
FastAPI WebSocket 엔드포인트와 전체 메시지 프로토콜 통합
"""

import asyncio
import json
import logging
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect, Depends
from fastapi.routing import APIRouter
from websocket.connection_manager import WebSocketManager, get_websocket_manager, WebSocketConnection
from websocket.message_router import MessageRouter
from websocket.game_handler import GameEventHandler, get_game_handler

logger = logging.getLogger(__name__)

# WebSocket 라우터
websocket_router = APIRouter()


class WebSocketProtocol:
    """WebSocket 프로토콜 관리자"""
    
    def __init__(self):
        self.websocket_manager = None
        self.message_router = None
        self.game_handler = None
        self.active_connections: Dict[str, WebSocketConnection] = {}
    
    def initialize(self, websocket_manager: WebSocketManager):
        """의존성 주입 및 초기화"""
        self.websocket_manager = websocket_manager
        self.message_router = MessageRouter(websocket_manager)
        self.game_handler = get_game_handler(websocket_manager)
        
        # 게임 관련 핸들러를 메시지 라우터에 연결
        self._register_game_handlers()
    
    def _register_game_handlers(self):
        """게임 핸들러를 메시지 라우터에 등록"""
        # 게임 핸들러와 메시지 라우터 연결
        # Phase 3에서 더 세밀한 통합 예정
        pass
    
    async def handle_websocket_connection(self, websocket: WebSocket, room_id: str = None, token: str = None):
        """WebSocket 연결 처리"""
        connection = None
        try:
            # 연결 및 인증
            headers = dict(websocket.headers)
            
            # 쿼리 파라미터에서 토큰을 가져와서 헤더에 추가
            if token:
                headers['authorization'] = f'Bearer {token}'
            
            connection = await self.websocket_manager.connect(websocket, headers)
            
            if not connection:
                return  # 인증 실패로 연결이 종료됨
            
            # 룸 참가 (선택적)
            if room_id:
                join_success = await self.websocket_manager.join_room(connection.user_id, room_id)
                if join_success:
                    # 게임 핸들러에 참가 알림
                    await self.game_handler.handle_join_game(room_id, connection.user_id, connection.nickname)
            
            # 메시지 처리 루프
            await self._message_loop(connection)
            
        except WebSocketDisconnect as e:
            logger.info(f"WebSocket 연결 종료: user_id={connection.user_id if connection else 'unknown'}, code={e.code}")
        except Exception as e:
            logger.error(f"WebSocket 연결 처리 중 오류: {e}")
        finally:
            # 연결 정리
            if connection:
                await self._cleanup_connection(connection, room_id)
    
    async def _message_loop(self, connection: WebSocketConnection):
        """메시지 수신 및 처리 루프"""
        try:
            while connection.is_active:
                try:
                    # 메시지 수신 (타임아웃 설정)
                    message_data = await asyncio.wait_for(
                        connection.websocket.receive_text(),
                        timeout=30.0  # 30초 타임아웃
                    )
                    
                    # JSON 파싱
                    try:
                        message = json.loads(message_data)
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON 파싱 오류 (user_id={connection.user_id}): {e}")
                        await connection.send_json({
                            "type": "error",
                            "data": {"error": "올바르지 않은 JSON 형식입니다"}
                        })
                        continue
                    
                    # 메시지 라우팅
                    await self.message_router.route_message(connection, message)
                    
                except asyncio.TimeoutError:
                    # 핑 체크
                    ping_success = await self.websocket_manager.ping_user(connection.user_id)
                    if not ping_success:
                        logger.info(f"핑 실패로 연결 종료: user_id={connection.user_id}")
                        break
                    
                except WebSocketDisconnect:
                    logger.info(f"클라이언트 연결 종료: user_id={connection.user_id}")
                    break
                    
                except Exception as e:
                    logger.error(f"메시지 처리 중 오류 (user_id={connection.user_id}): {e}")
                    await connection.send_json({
                        "type": "error",
                        "data": {"error": "메시지 처리 중 오류가 발생했습니다"}
                    })
                    
        except Exception as e:
            logger.error(f"메시지 루프 중 치명적 오류 (user_id={connection.user_id}): {e}")
            
    async def _cleanup_connection(self, connection: WebSocketConnection, room_id: str = None):
        """연결 정리"""
        try:
            user_id = connection.user_id
            
            # 게임에서 나가기
            if room_id:
                await self.game_handler.handle_leave_game(room_id, user_id)
            
            # WebSocket 관리자에서 연결 제거
            await self.websocket_manager.disconnect(user_id, "연결 정리")
            
            logger.info(f"연결 정리 완료: user_id={user_id}")
            
        except Exception as e:
            logger.error(f"연결 정리 중 오류: {e}")


# 전역 프로토콜 인스턴스
websocket_protocol = WebSocketProtocol()


@websocket_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = None,
    websocket_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """기본 WebSocket 엔드포인트"""
    # 프로토콜 초기화 (첫 연결시에만)
    if websocket_protocol.websocket_manager is None:
        websocket_protocol.initialize(websocket_manager)
    
    await websocket_protocol.handle_websocket_connection(websocket, token=token)


@websocket_router.websocket("/ws/rooms/{room_id}")
async def websocket_room_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str = None,
    websocket_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """룸별 WebSocket 엔드포인트"""
    # 프로토콜 초기화 (첫 연결시에만)
    if websocket_protocol.websocket_manager is None:
        websocket_protocol.initialize(websocket_manager)
    
    await websocket_protocol.handle_websocket_connection(websocket, room_id, token)


@websocket_router.get("/ws/stats")
async def websocket_stats(websocket_manager: WebSocketManager = Depends(get_websocket_manager)):
    """WebSocket 연결 통계"""
    try:
        connection_stats = websocket_manager.get_connection_stats()
        
        if websocket_protocol.message_router:
            handler_stats = websocket_protocol.message_router.get_handler_stats()
        else:
            handler_stats = {}
        
        return {
            "status": "active",
            "connections": connection_stats,
            "handlers": handler_stats,
            "protocol_initialized": websocket_protocol.websocket_manager is not None
        }
        
    except Exception as e:
        logger.error(f"WebSocket 통계 조회 중 오류: {e}")
        return {"status": "error", "message": str(e)}


@websocket_router.post("/ws/broadcast")
async def broadcast_message(
    message: Dict[str, Any],
    websocket_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """전체 브로드캐스트 (관리자용)"""
    try:
        sent_count = await websocket_manager.broadcast_to_all(message)
        return {
            "status": "success",
            "message": "브로드캐스트 완료",
            "sent_count": sent_count
        }
    except Exception as e:
        logger.error(f"브로드캐스트 중 오류: {e}")
        return {"status": "error", "message": str(e)}


@websocket_router.post("/ws/rooms/{room_id}/broadcast")
async def broadcast_to_room(
    room_id: str,
    message: Dict[str, Any],
    websocket_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """룸별 브로드캐스트 (관리자용)"""
    try:
        sent_count = await websocket_manager.broadcast_to_room(room_id, message)
        return {
            "status": "success",
            "message": f"룸 {room_id}에 브로드캐스트 완료",
            "sent_count": sent_count
        }
    except Exception as e:
        logger.error(f"룸 브로드캐스트 중 오류: {e}")
        return {"status": "error", "message": str(e)}


# WebSocket 라우터 export
def get_websocket_router():
    """WebSocket 라우터 반환"""
    return websocket_router