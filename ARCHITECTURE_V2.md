# 끄아(KKUA) V2 아키텍처 설계 문서

## 프로젝트 개요

**끄아(KKUA)**는 실시간 멀티플레이어 한국어 끝말잇기 게임으로, 아이템 시스템, 단어 검증, 실시간 타이머, 게임 리포트, 포괄적인 로깅 기능을 포함한 완전한 Pure WebSocket 아키텍처로 재설계됩니다.

## 핵심 설계 원칙

### 1. Pure WebSocket 아키텍처
- 모든 실시간 통신은 WebSocket을 통해 처리
- REST API는 정적 데이터(사용자 프로필, 설정) 조회에만 사용
- 단일 진실의 원천(Single Source of Truth) 패턴 적용

### 2. 이벤트 기반 상태 관리
- 모든 게임 액션은 WebSocket 메시지로 처리
- 클라이언트는 상태를 직접 변경하지 않고 이벤트만 발송
- 서버가 모든 상태 변경을 검증하고 브로드캐스트

### 3. 계층화된 데이터 저장
- **Redis**: 실시간 게임 상태, 세션 관리
- **PostgreSQL**: 영구 데이터, 게임 기록, 통계

## 시스템 아키텍처

### 백엔드 구조

```
backend/
├── main.py                 # FastAPI 앱 진입점
├── websocket/
│   ├── connection_manager.py     # WebSocket 연결 관리
│   ├── message_router.py         # 메시지 라우팅
│   └── game_handler.py          # 게임 이벤트 처리
├── services/
│   ├── game_engine.py           # 핵심 게임 로직
│   ├── word_validator.py        # 단어 검증 서비스
│   ├── item_system.py           # 아이템 시스템
│   ├── timer_service.py         # 실시간 타이머
│   ├── score_calculator.py      # 점수 계산
│   ├── game_logger.py           # 게임 로깅
│   └── report_generator.py      # 게임 리포트 생성
├── models/
│   ├── game_models.py           # 게임 관련 모델
│   ├── user_models.py           # 사용자 모델
│   ├── item_models.py           # 아이템 모델
│   └── dictionary_models.py     # 사전 모델
└── repositories/
    ├── game_repository.py       # 게임 데이터 저장소
    ├── user_repository.py       # 사용자 데이터 저장소
    └── dictionary_repository.py # 사전 데이터 저장소
```

### 프론트엔드 구조

```
frontend/src/
├── components/
│   ├── Game/
│   │   ├── GameBoard.js         # 게임 보드
│   │   ├── WordInput.js         # 단어 입력
│   │   ├── Timer.js             # 타이머 표시
│   │   ├── PlayerList.js        # 플레이어 목록
│   │   ├── ItemPanel.js         # 아이템 패널
│   │   └── GameReport.js        # 게임 리포트
│   └── UI/
│       ├── Loading.js           # 로딩 컴포넌트
│       └── ErrorBoundary.js     # 에러 처리
├── hooks/
│   ├── useGameWebSocket.js      # 게임 WebSocket 훅
│   ├── useGameState.js          # 게임 상태 관리
│   ├── useTimer.js              # 타이머 훅
│   └── useItems.js              # 아이템 관리 훅
├── stores/
│   ├── gameStore.js             # 게임 상태 스토어
│   ├── userStore.js             # 사용자 상태 스토어
│   └── uiStore.js               # UI 상태 스토어
└── utils/
    ├── websocket.js             # WebSocket 유틸리티
    ├── gameUtils.js             # 게임 유틸리티
    └── validation.js            # 클라이언트 검증
```

## 데이터베이스 스키마

### PostgreSQL 스키마

```sql
-- 사용자 테이블
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    nickname VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    total_games INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    total_score BIGINT DEFAULT 0
);

-- 게임 룸 테이블
CREATE TABLE game_rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    max_players INTEGER DEFAULT 4,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'waiting' -- waiting, playing, finished
);

-- 게임 세션 테이블
CREATE TABLE game_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID REFERENCES game_rooms(id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    winner_id INTEGER REFERENCES users(id),
    total_rounds INTEGER DEFAULT 0,
    game_data JSONB -- 게임 상세 데이터
);

-- 한국어 사전 테이블
CREATE TABLE korean_dictionary (
    id SERIAL PRIMARY KEY,
    word VARCHAR(100) UNIQUE NOT NULL,
    definition TEXT,
    difficulty_level INTEGER DEFAULT 1, -- 1: 쉬움, 2: 보통, 3: 어려움
    frequency_score INTEGER DEFAULT 0,  -- 사용 빈도
    word_type VARCHAR(20), -- 명사, 동사, 형용사 등
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 아이템 정의 테이블
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    rarity VARCHAR(20) NOT NULL, -- common, uncommon, rare, epic, legendary
    effect_type VARCHAR(30) NOT NULL, -- time_boost, score_multiplier, word_hint 등
    effect_value JSONB, -- 아이템 효과 값
    cooldown_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 사용자 아이템 인벤토리
CREATE TABLE user_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    item_id INTEGER REFERENCES items(id),
    quantity INTEGER DEFAULT 1,
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 게임 로그 테이블
CREATE TABLE game_logs (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES game_sessions(id),
    user_id INTEGER REFERENCES users(id),
    action_type VARCHAR(30) NOT NULL, -- word_submit, item_use, game_start 등
    action_data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    round_number INTEGER
);

-- 단어 제출 기록
CREATE TABLE word_submissions (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES game_sessions(id),
    user_id INTEGER REFERENCES users(id),
    word VARCHAR(100) NOT NULL,
    is_valid BOOLEAN NOT NULL,
    response_time_ms INTEGER,
    score_earned INTEGER DEFAULT 0,
    round_number INTEGER,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_game_logs_session_id ON game_logs(session_id);
CREATE INDEX idx_word_submissions_session_id ON word_submissions(session_id);
CREATE INDEX idx_korean_dictionary_word ON korean_dictionary(word);
CREATE INDEX idx_user_items_user_id ON user_items(user_id);
```

### Redis 데이터 구조

```
# 게임 룸 상태
game:room:{room_id} -> {
    "id": "room_id",
    "status": "waiting|playing|finished",
    "players": [
        {
            "user_id": 123,
            "nickname": "player1",
            "ready": true,
            "score": 0,
            "items": ["time_boost", "score_multiplier"]
        }
    ],
    "current_round": 1,
    "current_turn": 0,
    "timer_expires_at": "2024-01-01T12:00:00Z",
    "word_chain": ["사과", "과일", "일요일"],
    "used_words": ["사과", "과일", "일요일"],
    "game_settings": {
        "max_rounds": 10,
        "turn_time_limit": 30,
        "difficulty": "normal"
    }
}

# 활성 타이머
timer:{room_id} -> {
    "expires_at": "2024-01-01T12:00:00Z",
    "current_player": 123,
    "remaining_ms": 25000
}

# 사용자 세션
session:{user_id} -> {
    "user_id": 123,
    "nickname": "player1",
    "current_room": "room_id",
    "connected_at": "2024-01-01T11:30:00Z",
    "websocket_id": "ws_connection_id"
}

# 단어 검증 캐시
word:cache:{word} -> {
    "is_valid": true,
    "definition": "과일의 한 종류",
    "difficulty": 1,
    "last_char": "과"
}
```

## WebSocket 메시지 프로토콜

### 클라이언트 → 서버

```javascript
// 게임 참가
{
    "type": "join_game",
    "room_id": "uuid",
    "user_token": "jwt_token"
}

// 게임 시작
{
    "type": "start_game",
    "room_id": "uuid"
}

// 단어 제출
{
    "type": "submit_word",
    "room_id": "uuid",
    "word": "단어",
    "timestamp": "2024-01-01T12:00:00Z"
}

// 아이템 사용
{
    "type": "use_item",
    "room_id": "uuid",
    "item_id": "time_boost",
    "target_user_id": 123 // 선택적
}

// 게임 포기
{
    "type": "forfeit_game",
    "room_id": "uuid"
}
```

### 서버 → 클라이언트

```javascript
// 게임 상태 업데이트
{
    "type": "game_state_update",
    "room_id": "uuid",
    "game_state": {
        "status": "playing",
        "current_round": 3,
        "current_turn": 1,
        "players": [...],
        "word_chain": ["사과", "과일"],
        "timer": {
            "remaining_ms": 25000,
            "expires_at": "2024-01-01T12:00:00Z"
        }
    }
}

// 단어 제출 결과
{
    "type": "word_result",
    "room_id": "uuid",
    "user_id": 123,
    "word": "일요일",
    "is_valid": true,
    "score_earned": 150,
    "word_info": {
        "definition": "주일의 첫째 날",
        "difficulty": 2,
        "bonus_points": 50
    }
}

// 타이머 업데이트
{
    "type": "timer_update",
    "room_id": "uuid",
    "remaining_ms": 20000,
    "current_player": 456
}

// 아이템 사용 알림
{
    "type": "item_used",
    "room_id": "uuid",
    "user_id": 123,
    "item_type": "time_boost",
    "effect": "추가 10초 획득",
    "target_user_id": 456
}

// 게임 종료
{
    "type": "game_finished",
    "room_id": "uuid",
    "winner": {
        "user_id": 123,
        "nickname": "winner",
        "final_score": 1250
    },
    "final_scores": [...],
    "game_report": {
        "total_rounds": 8,
        "total_words": 32,
        "game_duration_ms": 480000,
        "statistics": {...}
    }
}

// 에러 메시지
{
    "type": "error",
    "code": "INVALID_WORD",
    "message": "이미 사용된 단어입니다",
    "details": {
        "word": "사과",
        "reason": "duplicate"
    }
}
```

## 핵심 서비스 상세

### 1. 게임 엔진 (game_engine.py)

```python
class GameEngine:
    def __init__(self, redis_client, db_session):
        self.redis = redis_client
        self.db = db_session
        self.word_validator = WordValidator()
        self.score_calculator = ScoreCalculator()
        self.timer_service = TimerService()
        
    async def start_game(self, room_id: str):
        """게임 시작 로직"""
        
    async def submit_word(self, room_id: str, user_id: int, word: str):
        """단어 제출 처리"""
        
    async def use_item(self, room_id: str, user_id: int, item_id: str):
        """아이템 사용 처리"""
        
    async def handle_timer_expire(self, room_id: str):
        """타이머 만료 처리"""
```

### 2. 단어 검증 서비스 (word_validator.py)

```python
class WordValidator:
    def __init__(self, dictionary_repo, redis_client):
        self.dictionary = dictionary_repo
        self.cache = redis_client
        
    async def validate_word(self, word: str, last_char: str, used_words: Set[str]):
        """단어 유효성 검증"""
        # 1. 캐시 확인
        # 2. 사전 검색
        # 3. 끝말잇기 규칙 확인
        # 4. 중복 사용 확인
        # 5. 결과 캐싱
        
    async def get_word_info(self, word: str):
        """단어 정보 조회"""
```

### 3. 아이템 시스템 (item_system.py)

```python
class ItemSystem:
    ITEM_EFFECTS = {
        'time_boost': {'type': 'timer_extend', 'value': 10},
        'score_multiplier': {'type': 'score_multiply', 'value': 2.0},
        'word_hint': {'type': 'hint_next_word', 'value': 1},
        'freeze_opponent': {'type': 'timer_reduce', 'value': 5}
    }
    
    async def use_item(self, user_id: int, item_id: str, target_user_id: int = None):
        """아이템 사용 로직"""
        
    async def get_user_items(self, user_id: int):
        """사용자 아이템 조회"""
```

### 4. 실시간 타이머 (timer_service.py)

```python
class TimerService:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.timers = {}  # room_id -> asyncio.Task
        
    async def start_timer(self, room_id: str, duration_ms: int):
        """타이머 시작"""
        
    async def extend_timer(self, room_id: str, additional_ms: int):
        """타이머 연장"""
        
    async def get_remaining_time(self, room_id: str):
        """남은 시간 조회"""
```

## 성능 최적화

### 1. Redis 최적화
- 게임 상태 JSON 직렬화 최적화
- 단어 검증 결과 캐싱 (TTL: 1시간)
- 연결 풀링 및 클러스터링

### 2. WebSocket 최적화
- 연결 풀 관리
- 메시지 배치 처리
- 압축 전송 (gzip)

### 3. 데이터베이스 최적화
- 읽기 전용 복제본 사용
- 게임 로그 배치 삽입
- 인덱스 최적화

## 보안 고려사항

### 1. 인증 및 권한
- JWT 토큰 기반 인증
- WebSocket 연결 시 토큰 검증
- 게임 액션 권한 확인

### 2. 입력 검증
- 모든 사용자 입력 검증
- SQL 인젝션 방지
- XSS 방지

### 3. 속도 제한
- 사용자별 메시지 속도 제한
- 아이템 사용 쿨다운
- 연결 수 제한

## 모니터링 및 로깅

### 1. 게임 이벤트 로깅
- 모든 게임 액션 기록
- 성능 메트릭 수집
- 에러 추적

### 2. 실시간 모니터링
- WebSocket 연결 상태
- Redis 메모리 사용량
- 데이터베이스 성능

### 3. 알람 시스템
- 시스템 장애 알림
- 부정 행위 감지
- 성능 임계값 초과

## 테스트 전략

### 1. 단위 테스트
- 각 서비스별 독립 테스트
- 모든 게임 로직 검증
- 90% 이상 코드 커버리지

### 2. 통합 테스트
- WebSocket 통신 테스트
- Redis-PostgreSQL 동기화
- 동시 사용자 시뮬레이션

### 3. 부하 테스트
- 1000명 동시 접속
- 100개 동시 게임 룸
- 메모리 누수 검사

## 배포 및 운영

### 1. 컨테이너화
- Docker 이미지 최적화
- 다단계 빌드
- 환경별 설정 분리

### 2. 무중단 배포
- Blue-Green 배포
- 헬스 체크
- 롤백 전략

### 3. 확장성
- 수평 확장 가능한 설계
- 로드 밸런싱
- 데이터베이스 샤딩

이 문서는 끄아(KKUA) V2의 완전한 아키텍처 설계를 담고 있으며, 모든 기능 요구사항과 기술적 고려사항을 포함합니다.