# WebSocket 로직 상세 문서

## 개요

KKUA 프로젝트의 실시간 통신은 WebSocket을 통해 구현되며, 게임방의 모든 실시간 기능(채팅, 상태 동기화, 게임 진행)을 담당합니다.

## 아키텍처 구조

### 백엔드 WebSocket 계층

```
gameroom_ws_router.py (FastAPI WebSocket 엔드포인트)
           ↓
GameRoomWebSocketFacade (통합 인터페이스)
           ↓
┌─ WebSocketConnectionManager (연결 관리)
├─ WordChainGameEngine (게임 로직)
└─ WebSocketMessageService (메시지 처리)
```

### 1. GameRoomWebSocketFacade (`websocket/connection_manager.py`)

**역할**: WebSocket과 게임 로직의 통합 인터페이스

```python
class GameRoomWebSocketFacade:
    """게임방 WebSocket 기능의 통합 인터페이스
    
    WebSocket 연결 관리와 게임 로직을 통합하여 
    상위 레벨에서 사용하기 쉬운 단일 인터페이스를 제공합니다.
    """
```

**주요 메서드**:
- `connect_user()`: 사용자 WebSocket 연결
- `disconnect_user()`: 사용자 연결 해제
- `handle_message()`: 메시지 라우팅 및 처리
- `broadcast_to_room()`: 방 전체 브로드캐스트

### 2. WebSocketConnectionManager (`websocket/websocket_manager.py`)

**역할**: WebSocket 연결의 생명주기 관리

```python
class WebSocketConnectionManager:
    """WebSocket 연결을 관리하는 클래스"""
    
    def __init__(self):
        # room_id -> {guest_id: websocket} 매핑
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
```

**핵심 기능**:
- 연결 추가/제거
- 방별 연결 관리
- 메시지 브로드캐스트
- 연결 상태 추적

### 3. WordChainGameEngine (`websocket/word_chain_manager.py`)

**역할**: 끝말잇기 게임 규칙 및 상태 관리

```python
class WordChainGameEngine:
    """끝말잇기 게임의 로직을 관리하는 클래스"""
    
    def __init__(self):
        # room_id -> GameState 매핑
        self.game_states: Dict[int, GameState] = {}
```

**게임 상태 관리**:
- 현재 플레이어 추적
- 사용된 단어 히스토리
- 게임 진행 상태
- 타이머 관리

### 4. WebSocketMessageService (`services/websocket_message_service.py`)

**역할**: WebSocket 메시지 타입별 처리 로직

**지원 메시지 타입**:
- `chat`: 채팅 메시지
- `word_chain`: 단어 입력
- `game_action`: 게임 액션 (준비, 시작 등)
- `ping/pong`: 연결 상태 확인

## 메시지 플로우

### 1. 연결 설정

```
1. 클라이언트: WebSocket 연결 요청
   ws://localhost:8000/ws/gamerooms/{room_id}

2. 서버: 세션 쿠키 검증
   - 유효하지 않으면 연결 거부
   - 유효하면 연결 수락

3. 서버: 연결 등록 및 알림
   - ConnectionManager에 연결 추가
   - 방 참가자들에게 입장 알림 브로드캐스트

4. 클라이언트: 연결 성공
   - 현재 방 상태 동기화
   - 참가자 목록 업데이트
```

### 2. 채팅 메시지 처리

```json
// 클라이언트 → 서버
{
  "type": "chat",
  "message": "안녕하세요!",
  "message_id": "12345-timestamp"
}

// 서버 → 모든 클라이언트
{
  "type": "chat",
  "guest_id": 12345,
  "nickname": "사용자",
  "message": "안녕하세요!",
  "timestamp": "2024-01-01T12:00:00Z",
  "message_id": "12345-timestamp"
}
```

### 3. 게임 액션 처리

```json
// 준비 상태 변경
{
  "type": "game_action",
  "action": "toggle_ready"
}

// 게임 시작
{
  "type": "game_action", 
  "action": "start_game"
}
```

### 4. 끝말잇기 게임 플로우

```json
// 단어 제출
{
  "type": "word_chain",
  "word": "사과",
  "timestamp": 1234567890
}

// 게임 상태 업데이트
{
  "type": "word_chain_update",
  "current_player_id": 12345,
  "last_word": "사과",
  "last_character": "과",
  "used_words": ["사과"],
  "valid": true,
  "message": "단어가 승인되었습니다"
}
```

## 프론트엔드 WebSocket 구현

### useGameRoomSocket Hook

**위치**: `frontend/src/hooks/useGameRoomSocket.js`

**역할**: WebSocket 연결 및 상태 관리를 위한 React Hook

```javascript
export default function useGameRoomSocket(roomId) {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [participants, setParticipants] = useState([]);
  // ... 기타 상태들
}
```

### 연결 생명주기

```javascript
useEffect(() => {
  if (roomId && isAuthenticated && user) {
    // WebSocket 연결 생성
    const socket = new WebSocket(
      `${process.env.REACT_APP_WS_BASE_URL}/ws/gamerooms/${roomId}`
    );
    
    socket.onopen = () => {
      setConnected(true);
      setRoomUpdated(true);
    };
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleMessage(data);
    };
    
    socket.onclose = () => {
      setConnected(false);
    };
  }
}, [roomId, isAuthenticated, user]);
```

### 메시지 처리

```javascript
const handleMessage = (data) => {
  switch (data.type) {
    case 'chat':
      setMessages(prev => [...prev, data]);
      break;
      
    case 'participants_update':
      setParticipants(data.participants);
      setRoomUpdated(true);
      break;
      
    case 'game_started':
      window.location.href = `/keaing/${data.room_id}`;
      break;
      
    case 'ready_status_changed':
      updateParticipantStatus(data);
      break;
      
    // ... 기타 메시지 타입들
  }
};
```

## 에러 처리 및 재연결

### 백엔드 에러 처리

```python
@router.websocket("/ws/gamerooms/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int):
    try:
        # 인증 확인
        if not user:
            await websocket.close(code=1008, reason="Authentication required")
            return
            
        # 방 존재 확인
        if not room:
            await websocket.close(code=1008, reason="Room not found")
            return
            
        # 연결 처리
        await manager.connect_user(room_id, user.guest_id, websocket)
        
        while True:
            data = await websocket.receive_text()
            await manager.handle_message(room_id, user, data)
            
    except WebSocketDisconnect:
        await manager.disconnect_user(room_id, user.guest_id)
    except Exception as e:
        await websocket.close(code=1011, reason=f"Server error: {str(e)}")
```

### 프론트엔드 재연결 로직

```javascript
const [reconnectAttempts, setReconnectAttempts] = useState(0);
const maxReconnectAttempts = 5;

socket.onclose = (event) => {
  setConnected(false);
  
  if (reconnectAttempts < maxReconnectAttempts) {
    setTimeout(() => {
      setReconnectAttempts(prev => prev + 1);
      // WebSocket 재연결 시도
    }, 1000 * Math.pow(2, reconnectAttempts)); // 지수 백오프
  }
};
```

## 상태 동기화 패턴

### 1. Optimistic Updates

클라이언트에서 즉시 UI 업데이트 후 서버 응답으로 확정

```javascript
const sendMessage = (message) => {
  // 1. 즉시 UI 업데이트 (Optimistic)
  setMessages(prev => [...prev, {
    ...message,
    pending: true
  }]);
  
  // 2. 서버로 전송
  socket.send(JSON.stringify(message));
};

// 3. 서버 응답으로 확정
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'chat_confirmed') {
    setMessages(prev => prev.map(msg => 
      msg.message_id === data.message_id 
        ? { ...msg, pending: false }
        : msg
    ));
  }
};
```

### 2. State Reconciliation

서버 상태와 클라이언트 상태 동기화

```javascript
useEffect(() => {
  if (connected && socketParticipants?.length > 0) {
    // 서버에서 받은 참가자 정보로 동기화
    setParticipants(socketParticipants);
  }
}, [connected, socketParticipants]);
```

## 성능 최적화

### 1. 메시지 배치 처리

```python
# 짧은 시간 내 다수 메시지를 배치로 처리
async def batch_broadcast(self, room_id: int, messages: List[dict]):
    if room_id not in self.active_connections:
        return
        
    batch_message = {
        "type": "batch_update",
        "messages": messages
    }
    
    await self.broadcast_to_room(room_id, batch_message)
```

### 2. 연결 상태 모니터링

```python
# 주기적 ping/pong으로 연결 상태 확인
async def ping_connections(self):
    for room_id, connections in self.active_connections.items():
        for guest_id, websocket in connections.items():
            try:
                await websocket.ping()
            except:
                await self.disconnect_user(room_id, guest_id)
```

### 3. 메모리 관리

```python
# 게임 종료 시 상태 정리
async def cleanup_room(self, room_id: int):
    # WebSocket 연결 정리
    if room_id in self.active_connections:
        del self.active_connections[room_id]
    
    # 게임 상태 정리
    if room_id in self.game_states:
        del self.game_states[room_id]
```

## 보안 고려사항

### 1. 인증 검증

```python
# WebSocket 연결 시 세션 쿠키 검증
session_token = None
for cookie in websocket.headers.get("cookie", "").split(";"):
    if "session_token" in cookie:
        session_token = cookie.split("=")[1].strip()
        break

if not session_token:
    await websocket.close(code=1008, reason="Authentication required")
    return
```

### 2. 입력 검증

```python
# 메시지 내용 검증
def validate_message(self, message_data: dict) -> bool:
    if message_data.get("type") not in ALLOWED_MESSAGE_TYPES:
        return False
    
    if "message" in message_data:
        if len(message_data["message"]) > MAX_MESSAGE_LENGTH:
            return False
    
    return True
```

### 3. Rate Limiting

```python
# 사용자별 메시지 전송 속도 제한
class RateLimiter:
    def __init__(self, max_messages: int = 10, window_seconds: int = 60):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self.user_messages = {}
    
    def is_allowed(self, user_id: int) -> bool:
        now = time.time()
        user_msgs = self.user_messages.get(user_id, [])
        
        # 윈도우 밖의 메시지 제거
        user_msgs = [ts for ts in user_msgs if now - ts < self.window_seconds]
        
        if len(user_msgs) >= self.max_messages:
            return False
        
        user_msgs.append(now)
        self.user_messages[user_id] = user_msgs
        return True
```

## 디버깅 및 모니터링

### 로깅 패턴

```python
import logging

logger = logging.getLogger(__name__)

async def handle_message(self, room_id: int, user: Guest, message: str):
    try:
        data = json.loads(message)
        logger.info(f"WebSocket message received", extra={
            "room_id": room_id,
            "user_id": user.guest_id,
            "message_type": data.get("type"),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # 메시지 처리 로직
        
    except Exception as e:
        logger.error(f"WebSocket message handling failed", extra={
            "room_id": room_id,
            "user_id": user.guest_id,
            "error": str(e),
            "message": message
        })
```

### 메트릭 수집

```python
# 연결 통계
@property
def connection_stats(self) -> dict:
    total_connections = sum(
        len(conns) for conns in self.active_connections.values()
    )
    
    return {
        "total_rooms": len(self.active_connections),
        "total_connections": total_connections,
        "rooms_with_connections": [
            {"room_id": room_id, "connection_count": len(conns)}
            for room_id, conns in self.active_connections.items()
        ]
    }
```

이 WebSocket 구현은 실시간 게임의 모든 요구사항을 충족하면서도 확장 가능하고 안정적인 아키텍처를 제공합니다.