from typing import Dict
from fastapi import WebSocket
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """WebSocket 연결의 생명주기를 관리하는 저수준 매니저

    순수한 연결 관리, 메시지 전송, 브로드캐스트 기능만 담당합니다.
    """

    def __init__(self):
        # 활성 연결 관리: {room_id: {guest_id: WebSocket}}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: int, guest_id: int):
        """웹소켓 연결을 등록합니다."""
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}

        self.active_connections[room_id][guest_id] = websocket
        logger.info(f"웹소켓 연결 등록: room_id={room_id}, guest_id={guest_id}")

    async def disconnect(self, websocket: WebSocket, room_id: int, guest_id: int):
        """웹소켓 연결을 제거합니다."""
        logger.info(f"웹소켓 연결 해제: room_id={room_id}, guest_id={guest_id}")

        if (
            room_id in self.active_connections
            and guest_id in self.active_connections[room_id]
        ):
            del self.active_connections[room_id][guest_id]

            # 방에 더 이상 연결이 없으면 방 삭제
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def send_personal_message(
        self, message: dict, websocket: WebSocket, guest_id: int = None
    ):
        """특정 웹소켓에 메시지를 전송합니다."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"개인 메시지 전송 실패: {e}", exc_info=True)

    async def broadcast_to_room(self, room_id: int, message: dict):
        """방의 모든 사용자에게 메시지를 브로드캐스트합니다."""
        if room_id not in self.active_connections:
            return

        # 메시지 형식 확인 및 기본값 설정
        if "type" not in message:
            message["type"] = "message"
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()

        # 닫힌 연결 추적
        closed_connections = []

        for guest_id, connection in self.active_connections[room_id].items():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(
                    f"메시지 전송 오류: {e} - room_id={room_id}, guest_id={guest_id}"
                )
                closed_connections.append(guest_id)

        # 닫힌 연결 제거
        for guest_id in closed_connections:
            self.active_connections[room_id].pop(guest_id, None)

    async def broadcast_room_update(
        self, room_id: int, update_type: str, data: dict = None
    ):
        """방 상태 업데이트를 브로드캐스트합니다."""
        message = {
            "type": update_type,
            "room_id": room_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if data:
            message.update(data)

        await self.broadcast_to_room(room_id, message)

    def get_room_connections(self, room_id: int) -> Dict[int, WebSocket]:
        """특정 방의 모든 연결을 반환합니다."""
        return self.active_connections.get(room_id, {})

    def get_connection_count(self, room_id: int) -> int:
        """특정 방의 연결 수를 반환합니다."""
        return len(self.active_connections.get(room_id, {}))
