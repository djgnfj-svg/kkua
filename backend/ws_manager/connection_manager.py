from typing import Dict, List, Set
from fastapi import WebSocket
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        # 활성 연결 관리: {room_id: {guest_id: WebSocket}}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
        self.user_connections: Dict[int, Dict] = {}  # guest_id: {room_id, websocket}
        
    async def connect(self, websocket, room_id, guest_id):
        """웹소켓 연결을 관리합니다."""
        # 게스트 생성 로직 제거
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        
        self.active_connections[room_id][guest_id] = websocket
        print(f"웹소켓 연결 등록: room_id={room_id}, guest_id={guest_id}")
        
        # 방 참가자 업데이트 브로드캐스트 (필요시)
        await self.broadcast_room_update(room_id, "user_joined", {
            "guest_id": guest_id
        })
        
    async def disconnect(self, websocket: WebSocket, room_id: int, guest_id: int):
        """웹소켓 연결 제거"""
        print(f"웹소켓 연결 해제: room_id={room_id}, guest_id={guest_id}")
        
        if room_id in self.active_connections and guest_id in self.active_connections[room_id]:
            del self.active_connections[room_id][guest_id]
            
            # 방에 더 이상 연결이 없으면 방 삭제
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        
        # 사용자 연결 정보 제거
        if guest_id in self.user_connections:
            del self.user_connections[guest_id]
            
        # 사용자 퇴장 알림
        await self.broadcast_to_room(
            room_id, 
            {"type": "user_left", "guest_id": guest_id, "timestamp": datetime.utcnow().isoformat()}
        )
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """특정 웹소켓에 메시지 전송"""
        await websocket.send_text(json.dumps(message))
    
    async def broadcast_to_room(self, room_id: int, message: dict):
        """방의 모든 사용자에게 메시지 전송"""
        if room_id in self.active_connections:
            # 메시지 형식 확인 및 누락된, 중요 필드 기본값 설정
            if 'type' not in message:
                message['type'] = 'message'
            if 'timestamp' not in message:
                message['timestamp'] = datetime.utcnow().isoformat()
            
            # 디버깅용 로그
            print(f"브로드캐스트 메시지: {json.dumps(message)}")
            
            for connection in self.active_connections[room_id].values():
                await connection.send_text(json.dumps(message))
    
    async def broadcast_room_update(self, room_id: int, update_type: str, data: dict = None):
        """방 상태 업데이트 알림"""
        message = {
            "type": update_type,
            "room_id": room_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        if data:
            message.update({"data": data})
        await self.broadcast_to_room(room_id, message)
        
    def get_user_connection(self, guest_id: int):
        """특정 사용자의 연결 정보 조회"""
        if guest_id in self.user_connections:
            return self.user_connections[guest_id]
        return None 