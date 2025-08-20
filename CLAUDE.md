# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the 끄아(KKUA) V2 project.

## Project Overview

**끄아 (KKUA) V2**는 Pure WebSocket 아키텍처로 완전히 재설계된 실시간 멀티플레이어 한국어 끝말잇기 게임입니다. 아이템 시스템, 단어 검증, 실시간 타이머, 게임 리포트, 포괄적인 로깅 기능을 포함합니다.

## 핵심 아키텍처 원칙

### 1. Pure WebSocket 아키텍처
- **모든 실시간 통신은 WebSocket으로만 처리**
- REST API는 정적 데이터 조회에만 사용
- 단일 진실의 원천(Single Source of Truth) 패턴

### 2. 이벤트 기반 상태 관리
- 모든 게임 액션은 WebSocket 메시지로 처리
- 클라이언트는 상태를 직접 변경하지 않고 이벤트만 발송
- 서버가 모든 상태 변경을 검증하고 브로드캐스트

### 3. 계층화된 데이터 저장
- **Redis**: 실시간 게임 상태, 세션 관리 (24시간 TTL)
- **PostgreSQL**: 영구 데이터, 게임 기록, 통계, 사용자 정보

## 기술 스택

### 백엔드
- **Python FastAPI** - 웹 프레임워크
- **WebSocket** - 실시간 통신
- **Redis** - 실시간 상태 관리
- **PostgreSQL** - 영구 데이터 저장
- **SQLAlchemy** - ORM
- **Pydantic** - 데이터 검증

### 프론트엔드
- **React** - UI 프레임워크
- **Zustand** - 상태 관리
- **WebSocket** - 실시간 통신
- **TailwindCSS** - 스타일링

### 배포
- **Docker Compose** - 컨테이너 오케스트레이션
- **nginx** - 리버스 프록시 (프로덕션)

## 개발 가이드

### 구현 순서 (필수 준수)
**반드시 IMPLEMENTATION_PROMPTS.md의 Phase 순서를 따라 개발하세요:**

1. **Phase 1**: 백엔드 핵심 인프라 구축 (DB 스키마, Redis, SQLAlchemy 모델)
2. **Phase 2**: WebSocket 인프라 구축 (연결 관리, 메시지 라우팅)
3. **Phase 3**: 게임 엔진 및 핵심 서비스 (게임 로직, 단어 검증, 타이머, 점수)
4. **Phase 4**: 아이템 시스템 구현
5. **Phase 5**: 게임 리포트 및 로깅 시스템
6. **Phase 6**: 프론트엔드 구현
7. **Phase 7**: 성능 최적화 및 테스트

### 기능 검증
**각 Phase 완료 후 FEATURE_CHECKLIST.md의 해당 체크리스트로 검증하세요.**

### 필수 기능 요구사항
- **아이템 시스템**: 5가지 희귀도, 다양한 효과 (시간 연장, 점수 배수 등)
- **단어 검증**: 한국어 사전 기반 유효성 검증, 끝말잇기 규칙
- **실시간 타이머**: 30초 턴 제한, 아이템으로 시간 조절 가능
- **게임 리포트**: 상세한 게임 통계 및 하이라이트
- **포괄적인 로깅**: 모든 게임 이벤트 기록

## 파일 구조

### 백엔드 구조 (Phase별로 생성)
```
backend/
├── main.py                          # FastAPI 앱 진입점
├── requirements.txt                 # Python 의존성
├── Dockerfile                       # Docker 설정
├── .env                            # 환경 변수
├── models/                         # SQLAlchemy 모델
│   ├── __init__.py
│   ├── user_models.py
│   ├── game_models.py
│   ├── item_models.py
│   └── dictionary_models.py
├── repositories/                   # 데이터 접근 계층
│   ├── __init__.py
│   ├── user_repository.py
│   ├── game_repository.py
│   └── dictionary_repository.py
├── services/                       # 비즈니스 로직
│   ├── __init__.py
│   ├── game_engine.py
│   ├── word_validator.py
│   ├── item_system.py
│   ├── timer_service.py
│   ├── score_calculator.py
│   ├── game_logger.py
│   └── report_generator.py
├── websocket/                      # WebSocket 관련
│   ├── __init__.py
│   ├── connection_manager.py
│   ├── message_router.py
│   └── game_handler.py
├── schemas/                        # Pydantic 스키마
│   ├── __init__.py
│   ├── user_schemas.py
│   ├── game_schemas.py
│   └── websocket_schemas.py
└── tests/                         # 테스트
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    └── test_websocket.py
```

### 프론트엔드 구조 (Phase 6에서 생성)
```
frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── Game/
│   │   │   ├── GameBoard.js
│   │   │   ├── WordInput.js
│   │   │   ├── Timer.js
│   │   │   ├── PlayerList.js
│   │   │   ├── ItemPanel.js
│   │   │   └── GameReport.js
│   │   └── UI/
│   │       ├── Loading.js
│   │       └── ErrorBoundary.js
│   ├── hooks/
│   │   ├── useGameWebSocket.js
│   │   ├── useGameState.js
│   │   ├── useTimer.js
│   │   └── useItems.js
│   ├── stores/
│   │   ├── gameStore.js
│   │   ├── userStore.js
│   │   └── uiStore.js
│   ├── utils/
│   │   ├── websocket.js
│   │   ├── gameUtils.js
│   │   └── validation.js
│   ├── App.js
│   ├── index.js
│   └── index.css
├── package.json
├── tailwind.config.js
└── Dockerfile
```

## WebSocket 메시지 프로토콜

### 클라이언트 → 서버 메시지
```javascript
// 게임 참가
{
    "type": "join_game",
    "room_id": "uuid",
    "user_token": "jwt_token"
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
    "target_user_id": 123
}
```

### 서버 → 클라이언트 메시지
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
```

## 개발 명령어

### 환경 설정
```bash
# 백엔드 환경 설정
cd backend
cp .env.example .env
# .env 파일에서 데이터베이스 URL, Redis URL 등 설정

# 프론트엔드 환경 설정 (Phase 6에서)
cd frontend
npm install
```

### Docker 개발 환경
```bash
# 전체 서비스 시작
docker-compose up -d

# 백엔드만 시작
docker-compose up -d backend db redis

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend

# 서비스 중지
docker-compose down
```

### 데이터베이스
```bash
# PostgreSQL 접속
docker exec -it kkua-db-1 psql -U postgres -d kkua_db

# Redis 접속
docker exec -it kkua-redis-1 redis-cli

# Redis 모니터링
docker exec kkua-redis-1 redis-cli monitor

# Redis 캐시 초기화
docker exec kkua-redis-1 redis-cli FLUSHDB
```

### 테스트
```bash
# 백엔드 테스트
cd backend
python -m pytest tests/ -v --cov=. --cov-report=html

# 프론트엔드 테스트 (Phase 6에서)
cd frontend
npm test
npm run test:coverage
```

## 코딩 규칙

### 백엔드 (Python)
- **타입 힌팅 필수**: 모든 함수에 타입 힌트 추가
- **비동기 처리**: async/await 사용
- **에러 처리**: 모든 예외 상황 처리
- **로깅**: 중요 이벤트 로그 기록
- **문서화**: docstring 작성

### 프론트엔드 (React)
- **함수형 컴포넌트**: hooks 사용
- **타입 안전성**: PropTypes 또는 TypeScript
- **상태 관리**: Zustand 사용
- **스타일링**: TailwindCSS 클래스 사용
- **에러 처리**: ErrorBoundary 활용

### 공통 규칙
- **보안**: 모든 사용자 입력 검증
- **성능**: 불필요한 리렌더링/요청 방지
- **테스트**: 새로운 기능에 대한 테스트 작성
- **문서화**: 복잡한 로직에 주석 추가

## 환경 변수

### 백엔드 (.env)
```bash
# 데이터베이스
DATABASE_URL=postgresql://postgres:password@db:5432/kkua_db

# Redis
REDIS_URL=redis://redis:6379/0

# 보안
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET=your-jwt-secret

# 환경
ENVIRONMENT=development
DEBUG=true

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### 프론트엔드
```bash
# API 연결
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws

# 개발 설정
CHOKIDAR_USEPOLLING=true
```

## 성능 요구사항

### 응답 시간
- WebSocket 메시지 처리: < 10ms
- 단어 검증: < 50ms
- 데이터베이스 쿼리: < 100ms
- 게임 상태 업데이트: < 20ms

### 확장성
- 동시 WebSocket 연결: 1,000개 이상
- 동시 활성 게임: 100개 이상
- 일일 게임 수: 10,000게임 이상

### 리소스
- 서버 메모리: < 2GB
- Redis 메모리: < 1GB
- CPU 사용률: < 70%

## 보안 체크리스트

- [ ] JWT 토큰 기반 인증
- [ ] 모든 사용자 입력 검증
- [ ] SQL 인젝션 방지 (SQLAlchemy ORM 사용)
- [ ] XSS 방지 (입력 sanitization)
- [ ] Rate limiting 적용
- [ ] 로그에 민감정보 노출 방지
- [ ] CORS 설정 적절히 구성

## 디버깅

### 일반적인 문제들
1. **WebSocket 연결 실패**: JWT 토큰 만료 확인
2. **Redis 연결 오류**: Redis 서비스 상태 확인
3. **데이터베이스 연결 실패**: DATABASE_URL 설정 확인
4. **게임 상태 동기화 문제**: Redis 캐시 초기화 시도

### 로그 확인
```bash
# 백엔드 로그
docker-compose logs -f backend

# Redis 명령어 모니터링
docker exec kkua-redis-1 redis-cli monitor

# 데이터베이스 쿼리 로그
# PostgreSQL 설정에서 log_statement = 'all' 활성화
```

## 중요 알림

⚠️ **개발 시 반드시 지켜야 할 사항들:**

1. **Phase 순서 준수**: IMPLEMENTATION_PROMPTS.md의 Phase 1부터 7까지 순차적으로 구현
2. **기능 검증**: 각 Phase 완료 후 FEATURE_CHECKLIST.md로 검증
3. **Pure WebSocket**: 모든 실시간 기능은 WebSocket으로만 구현
4. **이벤트 기반**: 클라이언트에서 직접 상태 변경 금지
5. **테스트 작성**: 새로운 기능에 대한 테스트 필수
6. **문서 업데이트**: 중요한 변경사항 시 이 파일 업데이트

## 다음 단계

현재 상태: 프로젝트 초기화 완료

**지금 진행해야 할 작업:**
1. **Phase 3 시작**: 게임 엔진 완성
   - 게임 로직 완성 및 통합
   - 단어 검증 서비스 구현
   - 실시간 타이머 시스템
   - 점수 계산 및 콤보 시스템

**Phase 2 완료 현황 (2024-08-20):**
✅ JWT 토큰 기반 인증 시스템 (auth.py)
✅ WebSocket 연결 관리자 (websocket/connection_manager.py)  
✅ 메시지 라우터 시스템 (websocket/message_router.py)
✅ 게임 이벤트 핸들러 (websocket/game_handler.py)
✅ WebSocket 엔드포인트 (websocket/websocket_endpoint.py)

IMPLEMENTATION_PROMPTS.md의 Phase 3 프롬프트를 참조하여 개발을 계속하세요.