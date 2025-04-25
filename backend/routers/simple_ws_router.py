from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
from datetime import datetime

router = APIRouter(
    prefix="/simple-ws",
    tags=["websocket-test"],
)

# 간단한 연결 관리자
class SimpleConnectionManager:
    def __init__(self):
        # 활성 연결 저장 (client_id: WebSocket)
        self.active_connections: Dict[str, WebSocket] = {}
        # 사용자 닉네임 저장
        self.user_names: Dict[str, str] = {}
        # 다음 클라이언트 ID
        self.next_client_id = 1
    
    def generate_client_id(self) -> str:
        """새 클라이언트 ID 생성"""
        client_id = f"client_{self.next_client_id}"
        self.next_client_id += 1
        return client_id
    
    async def connect(self, websocket: WebSocket) -> str:
        """새 클라이언트 연결 처리"""
        await websocket.accept()
        client_id = self.generate_client_id()
        self.active_connections[client_id] = websocket
        self.user_names[client_id] = f"사용자_{client_id}"
        
        print(f"새 연결 추가: {client_id}")
        return client_id
    
    def disconnect(self, client_id: str):
        """클라이언트 연결 해제"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        if client_id in self.user_names:
            del self.user_names[client_id]
            
        print(f"연결 종료: {client_id}")
    
    async def send_personal_message(self, message: dict, client_id: str):
        """특정 클라이언트에게 메시지 전송"""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps(message))
    
    async def broadcast(self, message: dict, exclude: str = None):
        """모든 클라이언트에게 메시지 브로드캐스트"""
        # 기본 메시지 필드 추가
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
            
        for client_id, connection in list(self.active_connections.items()):
            if exclude and client_id == exclude:
                continue  # 제외할 클라이언트 건너뛰기
                
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"메시지 전송 오류 ({client_id}): {str(e)}")
                # 오류 발생 시 연결 제거
                self.disconnect(client_id)
    
    def set_username(self, client_id: str, username: str) -> bool:
        """사용자 이름 설정"""
        if client_id in self.active_connections:
            self.user_names[client_id] = username
            return True
        return False
    
    def get_username(self, client_id: str) -> str:
        """사용자 이름 조회"""
        return self.user_names.get(client_id, f"손님_{client_id}")
    
    def get_active_users(self) -> List[dict]:
        """현재 활성 사용자 목록 반환"""
        return [
            {"client_id": client_id, "username": self.get_username(client_id)}
            for client_id in self.active_connections.keys()
        ]

# 연결 관리자 인스턴스 생성
connection_manager = SimpleConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """간단한 웹소켓 엔드포인트"""
    client_id = await connection_manager.connect(websocket)
    
    # 연결 성공 메시지
    await connection_manager.send_personal_message({
        "type": "connected",
        "client_id": client_id,
        "message": f"연결 성공! 당신의 ID는 {client_id}입니다.",
        "timestamp": datetime.utcnow().isoformat()
    }, client_id)
    
    # 새 사용자 입장 알림
    await connection_manager.broadcast({
        "type": "user_joined",
        "client_id": client_id,
        "username": connection_manager.get_username(client_id),
        "message": f"{connection_manager.get_username(client_id)}님이 입장했습니다.",
        "users": connection_manager.get_active_users()
    }, exclude=None)  # 모든 사용자에게 브로드캐스트
    
    try:
        # 메시지 수신 루프
        while True:
            # 메시지 수신
            data = await websocket.receive_text()
            message_data = json.loads(data)
            print(f"메시지 수신 from {client_id}: {message_data}")
            
            # 메시지 유형에 따른 처리
            message_type = message_data.get("type", "")
            
            if message_type == "chat":
                # 채팅 메시지 브로드캐스트
                chat_message = {
                    "type": "chat",
                    "client_id": client_id,
                    "username": connection_manager.get_username(client_id),
                    "message": message_data.get("message", ""),
                    "timestamp": datetime.utcnow().isoformat()
                }
                await connection_manager.broadcast(chat_message)
                
            elif message_type == "set_username":
                # 사용자 이름 설정
                new_username = message_data.get("username", "")
                if new_username:
                    old_username = connection_manager.get_username(client_id)
                    connection_manager.set_username(client_id, new_username)
                    
                    # 이름 변경 알림
                    await connection_manager.broadcast({
                        "type": "username_changed",
                        "client_id": client_id,
                        "old_username": old_username,
                        "new_username": new_username,
                        "message": f"{old_username}님이 이름을 {new_username}으로 변경했습니다.",
                        "users": connection_manager.get_active_users()
                    })
            
            elif message_type == "ping":
                # 핑-퐁 메시지
                await connection_manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }, client_id)
                
    except WebSocketDisconnect:
        # 연결 종료 처리
        username = connection_manager.get_username(client_id)
        connection_manager.disconnect(client_id)
        
        # 사용자 퇴장 알림
        await connection_manager.broadcast({
            "type": "user_left",
            "client_id": client_id,
            "username": username,
            "message": f"{username}님이 퇴장했습니다.",
            "users": connection_manager.get_active_users()
        })
    
    except Exception as e:
        # 기타 예외 처리
        print(f"웹소켓 오류 ({client_id}): {str(e)}")
        connection_manager.disconnect(client_id)

@router.get("/")
def get_test_page():
    """테스트 페이지 안내"""
    return {
        "message": "웹소켓 테스트 페이지는 /static/websocket_test.html에서 접근할 수 있습니다.",
        "websocket_url": "/simple-ws/ws"
    } 