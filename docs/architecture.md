# KKUA 시스템 아키텍처

## 전체 시스템 구조

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Client  │◄──►│   FastAPI       │◄──►│   PostgreSQL    │
│   (Frontend)    │    │   (Backend)     │    │   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │
         │                        │
         └────── WebSocket ───────┘
         
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Environment                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Frontend   │  │   Backend   │  │  Database   │            │
│  │   :3000     │  │    :8000    │  │    :5432    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

## 백엔드 아키텍처 (FastAPI)

### 레이어드 아키텍처

```
┌──────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │   Router    │  │ WebSocket   │  │ Middleware  │      │
│  │ (REST API)  │  │  Endpoint   │  │  (Auth,     │      │
│  │             │  │             │  │  Security)  │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└──────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────────────────────────────────────┐
│                     Business Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │   Service   │  │ WebSocket   │  │    Game     │      │
│  │   Logic     │  │  Message    │  │   Engine    │      │
│  │             │  │  Service    │  │             │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└──────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────────────────────────────────────┐
│                   Data Access Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ Repository  │  │  Database   │  │   Session   │      │
│  │   Pattern   │  │  Connection │  │   Manager   │      │
│  │             │  │             │  │             │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└──────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────────────────────────────────────┐
│                    Data Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ SQLAlchemy  │  │ PostgreSQL  │  │   Redis     │      │
│  │   Models    │  │  Database   │  │  (Future)   │      │
│  │             │  │             │  │             │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 핵심 컴포넌트

#### 1. 라우터 계층 (`routers/`)

```python
# API 엔드포인트 정의
routers/
├── auth_router.py          # 인증 (로그인, 로그아웃, 프로필)
├── gamerooms_router.py     # 게임방 CRUD
├── gameroom_actions_router.py  # 게임방 액션 (참가, 준비, 시작)
├── gameroom_ws_router.py   # WebSocket 엔드포인트
└── guests_router.py        # 게스트 관리
```

**설계 원칙**:
- Single Responsibility: 각 라우터는 하나의 도메인 담당
- Dependency Injection: 서비스 계층 의존성 주입
- Validation: Pydantic 스키마를 통한 입력 검증

#### 2. 서비스 계층 (`services/`)

```python
services/
├── auth_service.py         # 인증 및 세션 관리
├── gameroom_service.py     # 게임방 비즈니스 로직
├── guest_service.py        # 게스트 관리
├── session_service.py      # 세션 스토리지
├── game_state_service.py   # 게임 상태 관리
└── websocket_message_service.py  # WebSocket 메시지 처리
```

**비즈니스 로직 캡슐화**:
```python
class GameroomService:
    """게임방 관련 비즈니스 로직 처리"""
    
    def __init__(self, repository: GameroomRepository, ws_manager):
        self.repository = repository
        self.ws_manager = ws_manager
    
    async def create_room(self, room_data: dict, creator: Guest) -> Gameroom:
        """게임방 생성 및 생성자 자동 참가"""
        # 1. 방 생성
        room = self.repository.create(room_data)
        
        # 2. 생성자 참가
        self.repository.add_participant(room.room_id, creator.guest_id, is_creator=True)
        
        # 3. WebSocket 알림
        await self.ws_manager.notify_room_created(room)
        
        return room
```

#### 3. 리포지토리 계층 (`repositories/`)

```python
repositories/
├── gameroom_repository.py  # 게임방 데이터 접근
├── guest_repository.py     # 게스트 데이터 접근
└── game_log_repository.py  # 게임 결과 데이터 접근
```

**데이터 접근 추상화**:
```python
class GameroomRepository:
    """게임방 데이터 접근 레이어"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_room_participants(self, room_id: int) -> List[GameroomParticipant]:
        """활성 참가자 목록 조회"""
        return (
            self.db.query(GameroomParticipant)
            .filter(
                GameroomParticipant.room_id == room_id,
                GameroomParticipant.left_at.is_(None)
            )
            .all()
        )
```

#### 4. WebSocket 관리 (`websocket/`)

```python
websocket/
├── connection_manager.py   # GameRoomWebSocketFacade (통합 인터페이스)
├── websocket_manager.py    # WebSocketConnectionManager (연결 관리)
└── word_chain_manager.py   # WordChainGameEngine (게임 로직)
```

**Facade 패턴 적용**:
```python
class GameRoomWebSocketFacade:
    """WebSocket과 게임 로직의 통합 인터페이스"""
    
    def __init__(self):
        self.connection_manager = WebSocketConnectionManager()
        self.game_engine = WordChainGameEngine()
        self.message_service = WebSocketMessageService()
    
    async def handle_message(self, room_id: int, user: Guest, message: str):
        """메시지 타입에 따른 처리 위임"""
        data = json.loads(message)
        message_type = data.get("type")
        
        if message_type == "chat":
            await self.message_service.handle_chat(room_id, user, data)
        elif message_type == "word_chain":
            await self.game_engine.handle_word_submission(room_id, user, data)
        elif message_type == "game_action":
            await self.message_service.handle_game_action(room_id, user, data)
```

## 프론트엔드 아키텍처 (React)

### 컴포넌트 구조

```
src/
├── Pages/                  # 페이지별 컴포넌트
│   ├── Loading/           # 로그인 페이지
│   ├── Lobby/             # 게임 로비
│   ├── GameLobbyPage/     # 게임방 로비
│   ├── InGame/            # 게임 플레이
│   └── GameResult/        # 게임 결과
├── hooks/                 # 커스텀 훅
├── store/                 # 상태 관리 (Zustand)
├── Api/                   # API 통신
├── utils/                 # 유틸리티
└── contexts/              # React Context
```

### 페이지별 아키텍처 패턴

각 페이지는 다음 구조를 따릅니다:

```
Pages/[PageName]/
├── [PageName].js          # 메인 컴포넌트
├── components/            # 페이지 전용 컴포넌트
│   ├── ComponentA.js
│   └── ComponentB.js
└── hooks/                 # 페이지 전용 훅
    ├── usePageLogic.js
    └── usePageData.js
```

**예시: GameLobbyPage**
```javascript
// GameLobbyPage.js (메인 컴포넌트)
function GameLobbyPage() {
  const { 
    participants, 
    messages, 
    isOwner,
    handleStartGame,
    handleLeaveRoom 
  } = useGameLobby(); // 비즈니스 로직
  
  return (
    <div className="game-lobby">
      <ParticipantList participants={participants} />
      <ChatSection messages={messages} />
      <ActionButtons 
        isOwner={isOwner}
        onStart={handleStartGame}
        onLeave={handleLeaveRoom}
      />
    </div>
  );
}

// hooks/useGameLobby.js (비즈니스 로직)
const useGameLobby = () => {
  const { connected, participants, messages } = useGameRoomSocket(roomId);
  const { user } = useAuth();
  
  const isOwner = useMemo(() => 
    participants.find(p => p.guest_id === user.guest_id)?.is_creator || false,
    [participants, user]
  );
  
  const handleStartGame = useCallback(async () => {
    try {
      await axiosInstance.post(`/gamerooms/${roomId}/start`);
    } catch (error) {
      console.error('게임 시작 실패:', error);
    }
  }, [roomId]);
  
  return { participants, messages, isOwner, handleStartGame };
};
```

### 상태 관리 (Zustand)

```javascript
// store/guestStore.js
const useGuestStore = create((set, get) => ({
  // 상태
  guest: null,
  isAuthenticated: false,
  currentRoom: null,
  
  // 액션
  setGuest: (guest) => set({ guest, isAuthenticated: !!guest }),
  
  setCurrentRoom: (room) => set({ currentRoom: room }),
  
  logout: () => set({ 
    guest: null, 
    isAuthenticated: false, 
    currentRoom: null 
  }),
  
  // 계산된 값
  get guestId() {
    return get().guest?.guest_id;
  }
}));
```

### API 레이어

```javascript
// Api/axiosInstance.js
const axiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 5000,
  withCredentials: true, // 세션 쿠키 포함
});

// 인터셉터: 응답 처리
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 인증 실패 시 로그인 페이지로 리다이렉트
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);
```

## 데이터 플로우

### 1. 인증 플로우

```
1. 사용자 로그인 요청
   Frontend: authApi.login(nickname)
   
2. 서버 인증 처리
   Backend: AuthService.login()
   - 게스트 계정 생성/조회
   - 세션 토큰 생성
   - HTTP-only 쿠키 설정
   
3. 클라이언트 상태 업데이트
   Frontend: AuthContext.setUser()
   
4. 보호된 라우트 접근
   Frontend: AuthMiddleware 검증
   Backend: auth_middleware.py 검증
```

### 2. 게임방 생성 플로우

```
1. 사용자 방 생성 요청
   Frontend: RoomModal 폼 제출
   
2. API 호출
   Frontend: axiosInstance.post('/gamerooms', roomData)
   
3. 서버 처리
   Backend: GameroomService.create_room()
   - 방 생성 (Repository)
   - 생성자 자동 참가
   - 데이터베이스 저장
   
4. 응답 및 리다이렉트
   Frontend: navigate(gameLobbyUrl(roomId))
```

### 3. 실시간 게임 플로우

```
1. WebSocket 연결
   Frontend: useGameRoomSocket(roomId)
   Backend: GameRoomWebSocketFacade.connect_user()
   
2. 게임 상태 동기화
   Backend: 참가자 목록, 채팅 메시지 브로드캐스트
   Frontend: 상태 업데이트 및 UI 리렌더링
   
3. 사용자 액션
   Frontend: 단어 입력, 준비 상태 변경
   Backend: WordChainGameEngine.handle_word_submission()
   
4. 게임 상태 업데이트
   Backend: 게임 결과 계산 및 브로드캐스트
   Frontend: 게임 화면 업데이트
```

## 보안 아키텍처

### 1. 인증 & 인가

```python
# 세션 기반 인증
class AuthService:
    def create_session(self, guest: Guest) -> str:
        session_token = secrets.token_urlsafe(32)
        self.session_service.store_session(session_token, guest.guest_id)
        return session_token
    
    def validate_session(self, session_token: str) -> Optional[Guest]:
        guest_id = self.session_service.get_session(session_token)
        if guest_id:
            return self.guest_service.get_guest_by_id(guest_id)
        return None
```

### 2. WebSocket 보안

```python
# WebSocket 연결 시 인증 확인
@router.websocket("/ws/gamerooms/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int):
    # 쿠키에서 세션 토큰 추출
    session_token = extract_session_from_cookies(websocket.headers)
    
    # 세션 검증
    user = auth_service.validate_session(session_token)
    if not user:
        await websocket.close(code=1008, reason="Authentication required")
        return
```

### 3. CORS 설정

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # 환경별 설정
    allow_credentials=True,               # 쿠키 허용
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 성능 최적화

### 1. 데이터베이스 최적화

```python
# 인덱스 설정
class Gameroom(Base):
    __tablename__ = "gamerooms"
    
    room_id = Column(Integer, primary_key=True, index=True)
    created_by = Column(Integer, ForeignKey("guests.guest_id"), index=True)
    status = Column(String, index=True)  # 방 상태별 필터링을 위한 인덱스
    created_at = Column(DateTime, index=True)  # 정렬을 위한 인덱스

# 쿼리 최적화
def get_active_rooms(self, limit: int = 10) -> List[Gameroom]:
    return (
        self.db.query(Gameroom)
        .filter(Gameroom.status.in_(['WAITING', 'PLAYING']))  # 인덱스 활용
        .order_by(Gameroom.created_at.desc())
        .limit(limit)
        .all()
    )
```

### 2. 프론트엔드 최적화

```javascript
// React.memo로 불필요한 리렌더링 방지
const ParticipantItem = React.memo(({ participant }) => (
  <div className="participant">
    {participant.nickname}
    {participant.is_ready && <Badge>Ready</Badge>}
  </div>
));

// useMemo로 비싼 계산 캐싱
const sortedParticipants = useMemo(() => 
  participants.sort((a, b) => 
    Number(b.is_creator) - Number(a.is_creator)
  ),
  [participants]
);

// useCallback으로 함수 참조 안정화
const handleSendMessage = useCallback((message) => {
  if (connected && message.trim()) {
    sendMessage({
      type: 'chat',
      message: message.trim(),
      message_id: `${user.guest_id}-${Date.now()}`
    });
  }
}, [connected, user.guest_id, sendMessage]);
```

### 3. WebSocket 최적화

```python
# 메시지 배치 처리
class WebSocketConnectionManager:
    async def batch_broadcast(self, room_id: int, messages: List[dict]):
        """여러 메시지를 한 번에 전송"""
        if room_id not in self.active_connections:
            return
            
        batch_data = json.dumps({
            "type": "batch_update",
            "messages": messages
        })
        
        await self.broadcast_to_room(room_id, batch_data)

# 연결 풀링
class ConnectionPool:
    def __init__(self, max_connections: int = 1000):
        self.max_connections = max_connections
        self.active_count = 0
    
    async def can_accept_connection(self) -> bool:
        return self.active_count < self.max_connections
```

## 확장성 고려사항

### 1. 수평적 확장

```python
# Redis를 활용한 세션 공유 (Future)
class RedisSessionService:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def store_session(self, token: str, guest_id: int):
        self.redis.setex(f"session:{token}", 3600, guest_id)
    
    def get_session(self, token: str) -> Optional[int]:
        guest_id = self.redis.get(f"session:{token}")
        return int(guest_id) if guest_id else None
```

### 2. 마이크로서비스 분리 준비

```python
# 서비스별 독립적인 도메인 모델
# 게임 서비스
class GameService:
    """게임 로직만 담당하는 독립 서비스"""
    pass

# 채팅 서비스  
class ChatService:
    """채팅 기능만 담당하는 독립 서비스"""
    pass

# 알림 서비스
class NotificationService:
    """실시간 알림만 담당하는 독립 서비스"""
    pass
```

이 아키텍처는 현재 요구사항을 충족하면서도 미래의 확장성을 고려한 설계입니다.