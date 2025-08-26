"""
WebSocket 연결 관리자
JWT 인증 통합, 사용자 연결 추적, 룸별 그룹화, 자동 정리
"""

import asyncio
import logging
from typing import Dict, Set, Optional, Any, List
from fastapi import WebSocket, WebSocketDisconnect
from collections import defaultdict
from datetime import datetime, timezone
from auth import AuthService, extract_token_from_websocket_headers, AuthenticationError
from redis_models import RedisGameManager
from database import get_redis

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """개별 WebSocket 연결 정보"""
    
    def __init__(self, websocket: WebSocket, user_id: int, nickname: str, room_id: Optional[str] = None):
        self.websocket = websocket
        self.user_id = user_id
        self.nickname = nickname
        self.room_id = room_id
        self.connected_at = datetime.now(timezone.utc)
        self.last_ping = datetime.now(timezone.utc)
        self.is_active = True
    
    async def send_json(self, data: Dict[str, Any]) -> bool:
        """JSON 메시지 전송"""
        try:
            await self.websocket.send_json(data)
            return True
        except Exception as e:
            logger.error(f"메시지 전송 실패 (user_id={self.user_id}): {e}")
            self.is_active = False
            return False
    
    async def send_text(self, message: str) -> bool:
        """텍스트 메시지 전송"""
        try:
            await self.websocket.send_text(message)
            return True
        except Exception as e:
            logger.error(f"텍스트 메시지 전송 실패 (user_id={self.user_id}): {e}")
            self.is_active = False
            return False
    
    def update_ping(self):
        """마지막 핑 시간 업데이트"""
        self.last_ping = datetime.now(timezone.utc)
    
    def set_room(self, room_id: str):
        """룸 설정"""
        self.room_id = room_id


class WebSocketManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        self.auth_service = AuthService()
        self.redis_manager = RedisGameManager(get_redis())
        
        # 연결 추적
        self.active_connections: Dict[int, WebSocketConnection] = {}  # user_id -> connection
        self.room_connections: Dict[str, Set[int]] = defaultdict(set)  # room_id -> user_ids
        self.user_rooms: Dict[int, str] = {}  # user_id -> room_id
        
        # 정리 작업
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """정리 작업 시작"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_cleanup(self):
        """주기적 연결 정리"""
        while True:
            try:
                await asyncio.sleep(30)  # 30초마다 정리
                await self._cleanup_inactive_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"연결 정리 중 오류: {e}")
    
    async def _cleanup_inactive_connections(self):
        """비활성 연결 정리"""
        current_time = datetime.now(timezone.utc)
        inactive_users = []
        
        for user_id, connection in self.active_connections.items():
            # 5분 이상 핑이 없거나 비활성 상태인 연결
            if (current_time - connection.last_ping).seconds > 300 or not connection.is_active:
                inactive_users.append(user_id)
        
        for user_id in inactive_users:
            await self._remove_connection(user_id, "비활성 연결 정리")
    
    async def connect(self, websocket: WebSocket, headers: Dict[str, str]) -> Optional[WebSocketConnection]:
        """WebSocket 연결 및 인증"""
        try:
            # JWT 토큰 추출 및 검증
            token = extract_token_from_websocket_headers(headers)
            if not token:
                await websocket.close(code=4001, reason="인증 토큰이 필요합니다")
                return None
            
            user_info = self.auth_service.authenticate_websocket(token)
            user_id = user_info["user_id"]
            nickname = user_info["nickname"]
            
            # WebSocket 연결 수락
            await websocket.accept()
            
            # 기존 연결이 있다면 종료 (중복 연결 방지)
            if user_id in self.active_connections:
                existing_connection = self.active_connections[user_id]
                logger.info(f"중복 연결 감지: user_id={user_id}, nickname={nickname}. 기존 연결 종료 중...")
                
                # 기존 연결에 알림 전송
                await existing_connection.send_json({
                    "type": "connection_replaced",
                    "data": {
                        "reason": "다른 탭/창에서 새로운 연결이 생성되었습니다",
                        "message": "현재 연결이 종료됩니다"
                    }
                })
                
                await self._remove_connection(user_id, "새로운 연결로 교체")
            
            # 새 연결 생성
            connection = WebSocketConnection(websocket, user_id, nickname)
            self.active_connections[user_id] = connection
            
            logger.info(f"WebSocket 연결 성공: user_id={user_id}, nickname={nickname}")
            
            # 연결 확인 메시지 전송
            await connection.send_json({
                "type": "connection_established",
                "data": {
                    "user_id": user_id,
                    "nickname": nickname,
                    "connected_at": connection.connected_at.isoformat()
                }
            })
            
            return connection
            
        except AuthenticationError as e:
            logger.warning(f"WebSocket 인증 실패: {e}")
            await websocket.close(code=4001, reason=str(e))
            return None
        except Exception as e:
            logger.error(f"WebSocket 연결 중 오류: {e}")
            await websocket.close(code=4000, reason="연결 처리 중 오류가 발생했습니다")
            return None
    
    async def disconnect(self, user_id: int, reason: str = "사용자 연결 종료"):
        """WebSocket 연결 종료"""
        await self._remove_connection(user_id, reason)
    
    async def _remove_connection(self, user_id: int, reason: str):
        """연결 제거 (내부 메서드)"""
        try:
            connection = self.active_connections.get(user_id)
            if not connection:
                return
            
            # 명시적인 "방 나가기" 버튼을 눌렀을 때만 즉시 룸에서 제거
            if reason in ["명시적 방 나가기", "사용자 요청"]:
                if user_id in self.user_rooms:
                    room_id = self.user_rooms[user_id]
                    await self._leave_room(user_id, room_id)
            else:
                # 연결 끊김이나 기타 이유로는 30초 유예 기간
                if user_id in self.user_rooms:
                    room_id = self.user_rooms[user_id]
                    logger.info(f"WebSocket 연결 끊김: user_id={user_id}, room_id={room_id}, 30초 후 자동 퇴장")
                    
                    # 30초 후 자동 퇴장 스케줄링
                    import asyncio
                    async def delayed_leave():
                        await asyncio.sleep(30)
                        # 30초 후에도 연결이 복구되지 않았다면 방에서 나가기
                        if user_id not in self.active_connections:
                            logger.info(f"30초 후 자동 퇴장 실행: user_id={user_id}, room_id={room_id}")
                            if user_id in self.user_rooms and self.user_rooms[user_id] == room_id:
                                await self._leave_room(user_id, room_id)
                    
                    # 백그라운드로 실행
                    asyncio.create_task(delayed_leave())
            
            # 연결 종료
            if connection.is_active:
                try:
                    await connection.websocket.close()
                except:
                    pass  # 이미 종료된 연결일 수 있음
            
            # 연결 정보 제거
            del self.active_connections[user_id]
            
            logger.info(f"WebSocket 연결 종료: user_id={user_id}, reason={reason}")
            
        except Exception as e:
            logger.error(f"연결 제거 중 오류 (user_id={user_id}): {e}")
    
    async def join_room(self, user_id: int, room_id: str) -> bool:
        """룸 참가"""
        try:
            connection = self.active_connections.get(user_id)
            if not connection:
                logger.warning(f"활성 연결이 없는 사용자의 룸 참가 시도: user_id={user_id}")
                return False
            
            # 기존 룸에서 나가기
            if user_id in self.user_rooms:
                old_room_id = self.user_rooms[user_id]
                await self._leave_room(user_id, old_room_id)
            
            # 새 룸 참가
            self.room_connections[room_id].add(user_id)
            self.user_rooms[user_id] = room_id
            connection.set_room(room_id)
            
            # Redis에 참가 정보 업데이트
            await self.redis_manager.add_player_to_game(room_id, user_id, connection.nickname)
            
            # temporary_rooms의 플레이어 수 증가
            try:
                from datetime import datetime
                import main
                for room in main.temporary_rooms:
                    if room["id"] == room_id:
                        room["currentPlayers"] = min(room["maxPlayers"], room["currentPlayers"] + 1)
                        room["lastActivity"] = datetime.now().isoformat()
                        # 빈 방 마킹 제거 (플레이어가 들어왔으므로)
                        room.pop("emptyAt", None)
                        logger.info(f"WebSocket 방 참가: {room_id} - 현재 인원: {room['currentPlayers']}")
                        break
            except Exception as e:
                logger.warning(f"temporary_rooms 플레이어 수 업데이트 실패: {e}")
            
            logger.info(f"룸 참가: user_id={user_id}, room_id={room_id}")
            
            # 룸 참가 알림
            await self.broadcast_to_room(room_id, {
                "type": "user_joined_room",
                "data": {
                    "user_id": user_id,
                    "nickname": connection.nickname,
                    "room_id": room_id
                }
            }, exclude_user=user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"룸 참가 중 오류 (user_id={user_id}, room_id={room_id}): {e}")
            return False
    
    async def leave_room(self, user_id: int) -> bool:
        """현재 룸에서 나가기"""
        if user_id not in self.user_rooms:
            return False
        
        room_id = self.user_rooms[user_id]
        return await self._leave_room(user_id, room_id)
    
    async def _leave_room(self, user_id: int, room_id: str) -> bool:
        """룸 나가기 (내부 메서드)"""
        try:
            connection = self.active_connections.get(user_id)
            nickname = connection.nickname if connection else "Unknown"
            
            # 고도화된 방 나가기 처리
            from websocket.game_handler import get_game_handler
            game_handler = get_game_handler(self)
            
            should_continue, reason = await game_handler.handle_advanced_leave_room(room_id, user_id, nickname)
            
            # 기본 연결 정리 (항상 수행)
            if user_id in self.user_rooms and self.user_rooms[user_id] == room_id:
                del self.user_rooms[user_id]
            
            if user_id in self.room_connections[room_id]:
                self.room_connections[room_id].remove(user_id)
                
                # 빈 룸 정리
                if not self.room_connections[room_id]:
                    del self.room_connections[room_id]
            
            if connection:
                connection.room_id = None
            
            # temporary_rooms 동기화 (HTTP API와 WebSocket 상태 동기화) - early return 전에 수행
            try:
                import main
                for room in main.temporary_rooms:
                    if room["id"] == room_id:
                        room["currentPlayers"] = max(0, room["currentPlayers"] - 1)
                        current_count = room["currentPlayers"]
                        logger.info(f"temporary_rooms 동기화: {room_id} - 현재 인원: {current_count}")
                        
                        # 빈 방은 즉시 삭제하지 않고 마킹만
                        if room["currentPlayers"] == 0:
                            from datetime import datetime
                            room["lastActivity"] = datetime.now().isoformat()
                            room["emptyAt"] = datetime.now().isoformat()
                            logger.info(f"WebSocket 방 {room_id}이 비었음 - 자동 삭제 마킹")
                        break
            except Exception as e:
                logger.warning(f"temporary_rooms 동기화 실패: {e}")
            
            if not should_continue:
                # 방이 이미 삭제되었거나 특별 처리됨
                logger.info(f"방 나가기 특별 처리 완료: {reason}")
                return True
            
            # Redis에서 플레이어 제거 (방이 삭제되지 않은 경우만)
            await self.redis_manager.remove_player_from_game(room_id, user_id)
            
            logger.info(f"룸 나가기: user_id={user_id}, room_id={room_id}")
            
            # 업데이트된 게임 상태 브로드캐스트 (나가는 사용자 제외)
            from redis_models import RedisGameManager
            updated_game_state = await self.redis_manager.get_game_state(room_id)
            if updated_game_state:
                # 플레이어 목록을 프론트엔드 형식으로 변환
                players_list = []
                for player in updated_game_state.players:
                    players_list.append({
                        "id": str(player.user_id),
                        "user_id": player.user_id,
                        "nickname": player.nickname,
                        "score": player.score,
                        "isReady": player.status == "ready",
                        "isHost": player.is_host,
                        "words_submitted": player.words_submitted,
                        "max_combo": player.max_combo
                    })
                
                await self.broadcast_to_room(room_id, {
                    "type": "game_state_update",
                    "data": {
                        "room_id": room_id,
                        "status": updated_game_state.status,
                        "players": players_list,
                        "current_turn": updated_game_state.current_turn,
                        "current_round": updated_game_state.current_round,
                        "player_left_id": user_id  # 나간 플레이어 ID 표시
                    }
                }, exclude_user=user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"룸 나가기 중 오류 (user_id={user_id}, room_id={room_id}): {e}")
            return False
    
    async def send_to_user(self, user_id: int, message: Dict[str, Any]) -> bool:
        """특정 사용자에게 메시지 전송"""
        connection = self.active_connections.get(user_id)
        if not connection:
            logger.warning(f"존재하지 않는 사용자에게 메시지 전송 시도: user_id={user_id}")
            return False
        
        success = await connection.send_json(message)
        if not success:
            # 전송 실패시 연결 제거
            await self._remove_connection(user_id, "메시지 전송 실패")
        
        return success
    
    async def broadcast_to_room(self, room_id: str, message: Dict[str, Any], exclude_user: Optional[int] = None) -> int:
        """룸의 모든 사용자에게 브로드캐스트"""
        if room_id not in self.room_connections:
            logger.warning(f"존재하지 않는 룸에 브로드캐스트 시도: room_id={room_id}")
            return 0
        
        user_ids = list(self.room_connections[room_id])
        if exclude_user and exclude_user in user_ids:
            user_ids.remove(exclude_user)
        
        successful_sends = 0
        failed_users = []
        
        for user_id in user_ids:
            connection = self.active_connections.get(user_id)
            if connection:
                success = await connection.send_json(message)
                if success:
                    successful_sends += 1
                else:
                    failed_users.append(user_id)
        
        # 실패한 연결들 정리
        for user_id in failed_users:
            await self._remove_connection(user_id, "브로드캐스트 전송 실패")
        
        logger.debug(f"룸 브로드캐스트 완료: room_id={room_id}, 성공={successful_sends}, 실패={len(failed_users)}")
        return successful_sends
    
    async def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """모든 활성 연결에 브로드캐스트"""
        user_ids = list(self.active_connections.keys())
        successful_sends = 0
        
        for user_id in user_ids:
            success = await self.send_to_user(user_id, message)
            if success:
                successful_sends += 1
        
        logger.debug(f"전체 브로드캐스트 완료: 성공={successful_sends}")
        return successful_sends
    
    def get_room_users(self, room_id: str) -> List[Dict[str, Any]]:
        """룸의 사용자 목록 조회"""
        if room_id not in self.room_connections:
            return []
        
        users = []
        for user_id in self.room_connections[room_id]:
            connection = self.active_connections.get(user_id)
            if connection:
                users.append({
                    "user_id": user_id,
                    "nickname": connection.nickname,
                    "connected_at": connection.connected_at.isoformat()
                })
        
        return users
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """연결 통계 정보"""
        return {
            "total_connections": len(self.active_connections),
            "total_rooms": len(self.room_connections),
            "users_in_rooms": len(self.user_rooms),
            "room_stats": {
                room_id: len(user_ids) 
                for room_id, user_ids in self.room_connections.items()
            }
        }
    
    async def ping_user(self, user_id: int) -> bool:
        """사용자 연결 상태 확인"""
        connection = self.active_connections.get(user_id)
        if not connection:
            return False
        
        try:
            await connection.websocket.ping()
            connection.update_ping()
            return True
        except Exception as e:
            logger.warning(f"핑 실패 (user_id={user_id}): {e}")
            await self._remove_connection(user_id, "핑 응답 실패")
            return False
    
    async def close_all_connections(self):
        """모든 연결 종료 (서버 종료시 사용)"""
        user_ids = list(self.active_connections.keys())
        
        for user_id in user_ids:
            await self._remove_connection(user_id, "서버 종료")
        
        # 정리 작업 취소
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        
        logger.info("모든 WebSocket 연결이 종료되었습니다")


# 전역 WebSocket 관리자 인스턴스
websocket_manager = WebSocketManager()


async def get_websocket_manager() -> WebSocketManager:
    """WebSocket 관리자 의존성"""
    return websocket_manager