# 인증 시스템 문서

## 개요

KKUA는 세션 기반 인증 시스템을 사용합니다. UUID 기반 시스템에서 보안성이 강화된 세션 쿠키 방식으로 전환하여 더 안전하고 확장 가능한 인증을 제공합니다.

## 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Session       │
│   (React)       │    │   (FastAPI)     │    │   Storage       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         │ 1. 로그인 요청          │                        │
         ├────────────────────────►│                        │
         │                        │ 2. 세션 생성             │
         │                        ├────────────────────────►│
         │                        │ 3. 세션 저장             │
         │                        │◄────────────────────────┤
         │ 4. 쿠키 설정            │                        │
         │◄────────────────────────┤                        │
         │                        │                        │
         │ 5. API 요청 (쿠키 포함)  │                        │
         ├────────────────────────►│                        │
         │                        │ 6. 세션 검증             │
         │                        ├────────────────────────►│
         │                        │ 7. 사용자 정보 반환       │
         │                        │◄────────────────────────┤
         │ 8. 응답                │                        │
         │◄────────────────────────┤                        │
```

## 인증 컴포넌트

### 1. AuthService (`services/auth_service.py`)

**역할**: 인증 관련 핵심 비즈니스 로직

```python
class AuthService:
    """인증 서비스 - 로그인, 로그아웃, 세션 관리"""
    
    def __init__(self, guest_service: GuestService, session_service: SessionService):
        self.guest_service = guest_service
        self.session_service = session_service
    
    async def login(self, nickname: str) -> tuple[Guest, str]:
        """로그인 처리 (게스트 계정 생성/조회 + 세션 생성)"""
        
        # 1. 게스트 계정 확인/생성
        guest = await self.guest_service.get_or_create_guest(nickname)
        
        # 2. 새 세션 토큰 생성
        session_token = self._generate_session_token()
        
        # 3. 세션 저장
        await self.session_service.store_session(session_token, guest.guest_id)
        
        # 4. 게스트 테이블에 세션 토큰 업데이트
        await self.guest_service.update_session_token(guest.guest_id, session_token)
        
        return guest, session_token
    
    async def logout(self, session_token: str) -> bool:
        """로그아웃 처리 (세션 삭제)"""
        
        # 1. 세션에서 사용자 ID 조회
        guest_id = await self.session_service.get_session(session_token)
        
        if guest_id:
            # 2. 세션 삭제
            await self.session_service.delete_session(session_token)
            
            # 3. 게스트 테이블의 세션 토큰 초기화
            await self.guest_service.update_session_token(guest_id, None)
            
            return True
        
        return False
    
    async def validate_session(self, session_token: str) -> Optional[Guest]:
        """세션 토큰 검증 및 사용자 정보 반환"""
        
        if not session_token:
            return None
        
        # 1. 세션에서 사용자 ID 조회
        guest_id = await self.session_service.get_session(session_token)
        
        if not guest_id:
            return None
        
        # 2. 사용자 정보 조회
        guest = await self.guest_service.get_guest_by_id(guest_id)
        
        # 3. 게스트 테이블의 세션 토큰과 일치하는지 확인 (추가 보안)
        if guest and guest.session_token == session_token:
            return guest
        
        return None
    
    def _generate_session_token(self) -> str:
        """안전한 세션 토큰 생성"""
        return secrets.token_urlsafe(32)  # 256비트 토큰
```

### 2. SessionService (`services/session_service.py`)

**역할**: 세션 데이터 저장 및 관리

```python
class SessionService:
    """세션 저장소 관리 (현재: 메모리, 향후: Redis)"""
    
    def __init__(self):
        # 메모리 기반 세션 저장소 (개발용)
        self.sessions: Dict[str, SessionData] = {}
        self.session_lock = asyncio.Lock()
    
    async def store_session(self, session_token: str, guest_id: int, 
                          expires_in_seconds: int = 86400) -> bool:
        """세션 저장 (기본 24시간 유효)"""
        
        async with self.session_lock:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in_seconds)
            
            self.sessions[session_token] = SessionData(
                guest_id=guest_id,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                last_accessed=datetime.utcnow()
            )
            
            return True
    
    async def get_session(self, session_token: str) -> Optional[int]:
        """세션에서 guest_id 조회"""
        
        async with self.session_lock:
            session_data = self.sessions.get(session_token)
            
            if not session_data:
                return None
            
            # 만료 확인
            if datetime.utcnow() > session_data.expires_at:
                del self.sessions[session_token]
                return None
            
            # 마지막 접근 시간 업데이트
            session_data.last_accessed = datetime.utcnow()
            
            return session_data.guest_id
    
    async def delete_session(self, session_token: str) -> bool:
        """세션 삭제"""
        
        async with self.session_lock:
            if session_token in self.sessions:
                del self.sessions[session_token]
                return True
            return False
    
    async def cleanup_expired_sessions(self):
        """만료된 세션 정리 (백그라운드 태스크)"""
        
        async with self.session_lock:
            now = datetime.utcnow()
            expired_tokens = [
                token for token, data in self.sessions.items()
                if now > data.expires_at
            ]
            
            for token in expired_tokens:
                del self.sessions[token]
            
            return len(expired_tokens)

@dataclass
class SessionData:
    guest_id: int
    created_at: datetime
    expires_at: datetime
    last_accessed: datetime
```

### 3. Auth Middleware (`middleware/auth_middleware.py`)

**역할**: 요청별 인증 상태 검증

```python
class AuthMiddleware:
    """인증 미들웨어 - 모든 요청에서 인증 상태 확인"""
    
    def __init__(self, app, auth_service: AuthService):
        self.app = app
        self.auth_service = auth_service
        
        # 인증이 필요 없는 경로들
        self.public_paths = {
            "/", "/auth/login", "/auth/status", "/docs", "/redoc", 
            "/openapi.json", "/health", "/static"
        }
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        path = request.url.path
        
        # 공개 경로는 인증 스킵
        if self._is_public_path(path):
            await self.app(scope, receive, send)
            return
        
        # 세션 토큰 추출
        session_token = self._extract_session_token(request)
        
        # 세션 검증
        user = await self.auth_service.validate_session(session_token)
        
        if not user:
            # 인증 실패 응답
            response = JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"}
            )
            await response(scope, receive, send)
            return
        
        # 인증된 사용자 정보를 request.state에 저장
        request.state.user = user
        
        await self.app(scope, receive, send)
    
    def _extract_session_token(self, request: Request) -> Optional[str]:
        """요청에서 세션 토큰 추출"""
        return request.cookies.get("session_token")
    
    def _is_public_path(self, path: str) -> bool:
        """공개 경로 확인"""
        return any(path.startswith(public_path) for public_path in self.public_paths)
```

## 인증 플로우

### 1. 로그인 플로우

```python
# 1. 클라이언트 로그인 요청
POST /auth/login
{
    "nickname": "사용자닉네임"
}

# 2. 서버 처리 (auth_router.py)
@router.post("/login")
async def login(request: LoginRequest, response: Response):
    try:
        # 로그인 처리
        guest, session_token = await auth_service.login(request.nickname)
        
        # HTTP-only 쿠키 설정
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,      # JavaScript 접근 불가
            secure=True,        # HTTPS only (production)
            samesite="lax",     # CSRF 보호
            max_age=86400       # 24시간
        )
        
        return {
            "status": "success",
            "data": {
                "guest_id": guest.guest_id,
                "nickname": guest.nickname,
                "uuid": guest.uuid
            },
            "message": "로그인 성공"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 2. 로그아웃 플로우

```python
@router.post("/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    
    if session_token:
        await auth_service.logout(session_token)
    
    # 쿠키 삭제
    response.delete_cookie("session_token")
    
    return {
        "status": "success",
        "message": "로그아웃 완료"
    }
```

### 3. 인증 상태 확인

```python
@router.get("/me")
async def get_current_user(request: Request):
    # 미들웨어에서 이미 검증된 사용자 정보
    user = request.state.user
    
    return {
        "status": "success",
        "data": {
            "guest_id": user.guest_id,
            "nickname": user.nickname,
            "uuid": user.uuid
        }
    }

@router.get("/status")
async def check_auth_status(request: Request):
    session_token = request.cookies.get("session_token")
    
    if session_token:
        user = await auth_service.validate_session(session_token)
        return {
            "status": "success",
            "data": {
                "is_authenticated": user is not None,
                "guest_id": user.guest_id if user else None
            }
        }
    
    return {
        "status": "success",
        "data": {
            "is_authenticated": False,
            "guest_id": None
        }
    }
```

## WebSocket 인증

### WebSocket 연결 시 인증

```python
@router.websocket("/ws/gamerooms/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int):
    
    # 1. 쿠키에서 세션 토큰 추출
    session_token = None
    cookie_header = websocket.headers.get("cookie", "")
    
    for cookie in cookie_header.split(";"):
        if "session_token" in cookie:
            session_token = cookie.split("=")[1].strip()
            break
    
    # 2. 세션 검증
    user = await auth_service.validate_session(session_token)
    
    if not user:
        await websocket.close(code=1008, reason="Authentication required")
        return
    
    # 3. 게임방 접근 권한 확인
    room = await gameroom_service.get_room_by_id(room_id)
    if not room:
        await websocket.close(code=1008, reason="Room not found")
        return
    
    # 4. 참가자 확인
    is_participant = await gameroom_service.is_participant(room_id, user.guest_id)
    if not is_participant:
        await websocket.close(code=1008, reason="Not a participant")
        return
    
    # 5. WebSocket 연결 승인
    await websocket.accept()
    
    try:
        await manager.connect_user(room_id, user.guest_id, websocket)
        
        while True:
            data = await websocket.receive_text()
            await manager.handle_message(room_id, user, data)
            
    except WebSocketDisconnect:
        await manager.disconnect_user(room_id, user.guest_id)
```

## 프론트엔드 인증

### AuthContext (`contexts/AuthContext.js`)

```javascript
const AuthContext = createContext();

function authReducer(state, action) {
  switch (action.type) {
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload.user,
        loading: false,
        error: null
      };
    
    case 'LOGOUT':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        loading: false,
        error: null
      };
    
    case 'AUTH_ERROR':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        loading: false,
        error: action.payload.error
      };
    
    default:
      return state;
  }
}

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, {
    isAuthenticated: false,
    user: null,
    loading: true,
    error: null
  });

  // 앱 시작 시 인증 상태 확인
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await axiosInstance.get('/auth/status');
      
      if (response.data.data.is_authenticated) {
        const userResponse = await axiosInstance.get('/auth/me');
        dispatch({
          type: 'LOGIN_SUCCESS',
          payload: { user: userResponse.data.data }
        });
      } else {
        dispatch({ type: 'LOGOUT' });
      }
    } catch (error) {
      dispatch({ type: 'AUTH_ERROR', payload: { error: error.message } });
    }
  };

  const login = async (nickname) => {
    try {
      const response = await axiosInstance.post('/auth/login', { nickname });
      
      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: { user: response.data.data }
      });
      
      return response.data.data;
    } catch (error) {
      dispatch({ type: 'AUTH_ERROR', payload: { error: error.message } });
      throw error;
    }
  };

  const logout = async () => {
    try {
      await axiosInstance.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      dispatch({ type: 'LOGOUT' });
    }
  };

  return (
    <AuthContext.Provider value={{
      ...state,
      login,
      logout,
      checkAuthStatus
    }}>
      {children}
    </AuthContext.Provider>
  );
}
```

### Axios 인터셉터

```javascript
// Api/axiosInstance.js
const axiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 5000,
  withCredentials: true,  // 쿠키 자동 포함
});

// 응답 인터셉터: 인증 오류 처리
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

## 보안 고려사항

### 1. 세션 토큰 보안

```python
# 강력한 토큰 생성
def _generate_session_token(self) -> str:
    return secrets.token_urlsafe(32)  # 256비트 엔트로피

# 토큰 검증 시 타이밍 공격 방지
def _secure_compare(self, a: str, b: str) -> bool:
    return secrets.compare_digest(a.encode(), b.encode())
```

### 2. 쿠키 보안 설정

```python
response.set_cookie(
    key="session_token",
    value=session_token,
    httponly=True,          # XSS 방지
    secure=is_production,   # HTTPS only
    samesite="lax",         # CSRF 방지
    max_age=86400,          # 명시적 만료시간
    domain=None             # 도메인 제한
)
```

### 3. 세션 하이재킹 방지

```python
class SessionService:
    async def validate_session_security(self, session_token: str, 
                                      request_info: dict) -> bool:
        """세션 보안 검증"""
        session_data = self.sessions.get(session_token)
        
        if not session_data:
            return False
        
        # IP 주소 검증 (선택적)
        if session_data.ip_address != request_info.get('ip'):
            await self.delete_session(session_token)
            return False
        
        # User-Agent 검증 (선택적)
        if session_data.user_agent != request_info.get('user_agent'):
            await self.delete_session(session_token)
            return False
        
        return True
```

### 4. Rate Limiting

```python
class AuthRateLimiter:
    """인증 관련 Rate Limiting"""
    
    def __init__(self):
        self.login_attempts = {}  # IP -> (count, last_attempt)
        self.max_attempts = 5
        self.window_minutes = 15
    
    def check_login_rate_limit(self, ip_address: str) -> bool:
        now = datetime.utcnow()
        
        if ip_address in self.login_attempts:
            count, last_attempt = self.login_attempts[ip_address]
            
            # 윈도우 리셋
            if now - last_attempt > timedelta(minutes=self.window_minutes):
                self.login_attempts[ip_address] = (1, now)
                return True
            
            # 제한 초과 확인
            if count >= self.max_attempts:
                return False
            
            # 카운트 증가
            self.login_attempts[ip_address] = (count + 1, now)
        else:
            self.login_attempts[ip_address] = (1, now)
        
        return True
```

## 확장성 고려사항

### Redis 기반 세션 저장소 (향후)

```python
class RedisSessionService:
    """Redis 기반 세션 서비스 (분산 환경 지원)"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def store_session(self, session_token: str, guest_id: int, 
                          expires_in_seconds: int = 86400) -> bool:
        session_data = {
            "guest_id": guest_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat()
        }
        
        await self.redis.setex(
            f"session:{session_token}",
            expires_in_seconds,
            json.dumps(session_data)
        )
        
        return True
    
    async def get_session(self, session_token: str) -> Optional[int]:
        data = await self.redis.get(f"session:{session_token}")
        
        if data:
            session_data = json.loads(data)
            
            # 마지막 접근 시간 업데이트
            session_data["last_accessed"] = datetime.utcnow().isoformat()
            await self.redis.setex(
                f"session:{session_token}",
                86400,  # TTL 갱신
                json.dumps(session_data)
            )
            
            return session_data["guest_id"]
        
        return None
```

이 인증 시스템은 보안성과 확장성을 모두 고려하여 설계되었으며, 현재 요구사항을 충족하면서도 미래의 확장을 지원합니다.