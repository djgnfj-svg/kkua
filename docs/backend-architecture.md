# 백엔드 아키텍처 구조도

## 전체 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────┐
│                        KKUA Backend                            │
│                    (FastAPI + PostgreSQL + Redis)              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │───▶│   Routers   │───▶│  Services   │───▶│ Repositories│
│  (React)    │    │ (API Layer) │    │ (Business)  │    │ (Data Layer)│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                   │ Middleware  │    │  WebSocket  │    │   Models    │
                   │ (Auth/CORS) │    │  Manager    │    │ (SQLAlchemy)│
                   └─────────────┘    └─────────────┘    └─────────────┘
                                              │                   │
                                              ▼                   ▼
                                      ┌─────────────┐    ┌─────────────┐
                                      │    Redis    │    │ PostgreSQL  │
                                      │ (Real-time) │    │(Persistent) │
                                      └─────────────┘    └─────────────┘
```

## 계층별 상세 구조

### 1. API Layer (Routers)
```
routers/
├── auth_router.py              # 인증 관리
├── gamerooms_router.py         # 게임방 CRUD
├── gameroom_actions_router.py  # 게임방 액션 (참가/준비/시작)
├── gameroom_ws_router.py       # WebSocket 연결
├── game_api_router.py          # Redis 기반 게임 API
├── guests_router.py            # 사용자 관리
├── csrf_router.py              # CSRF 토큰
├── friendship_router.py        # 친구 시스템 ✨ NEW
├── game_mode_router.py         # 게임 모드 관리 ✨ NEW
└── item_router.py              # 아이템 시스템 ✨ NEW
```

### 2. Business Logic Layer (Services)
```
services/
├── auth_service.py                    # 인증 및 세션 관리
├── gameroom_service.py               # 게임방 통합 관리
├── guest_service.py                  # 사용자 서비스
├── session_service.py                # 세션 저장소
├── game_state_service.py             # 게임 상태 관리
├── websocket_message_service.py      # WebSocket 메시지 처리
├── redis_game_service.py             # Redis 실시간 게임
├── game_data_persistence_service.py  # 게임 결과 영속화
├── friendship_service.py             # 친구 관계 관리 ✨ NEW
├── game_mode_service.py              # 게임 모드 로직 ✨ NEW
├── item_service.py                   # 아이템 관리 ✨ NEW
└── advanced_score_service.py         # 고급 점수 계산 ✨ NEW
```

### 3. Data Access Layer (Repositories)
```
repositories/
├── gameroom_repository.py        # 게임방 데이터 접근
├── guest_repository.py           # 사용자 데이터 접근
├── game_log_repository.py        # 게임 로그 데이터 접근
├── friendship_repository.py      # 친구 관계 데이터 접근 ✨ NEW
└── player_profile_repository.py  # 플레이어 프로필 데이터 접근 ✨ NEW
```

### 4. Database Models (SQLAlchemy)
```
models/
├── guest_model.py              # 사용자 모델 (관리자 권한 추가)
├── gameroom_model.py           # 게임방 및 참가자 모델
├── game_log_model.py           # 게임 로그 모델
├── player_game_stats_model.py  # 플레이어별 게임 통계
├── word_chain_entry_model.py   # 단어 체인 엔트리
├── friendship_model.py         # 친구 관계 모델 ✨ NEW
├── game_mode_model.py          # 게임 모드 모델 ✨ NEW
├── item_model.py               # 아이템 모델 ✨ NEW
└── player_profile_model.py     # 플레이어 프로필 모델 ✨ NEW
```

### 5. Middleware & Security
```
middleware/
├── auth_middleware.py           # 세션 기반 인증 (관리자 권한 추가)
├── exception_handler.py         # 글로벌 예외 처리
├── rate_limiter.py             # API 속도 제한
├── csrf_middleware.py          # CSRF 보호
├── logging_middleware.py       # 요청/응답 로깅
└── security_headers_middleware.py # 보안 헤더
```

### 6. WebSocket Management
```
websocket/
├── connection_manager.py       # 게임방 WebSocket 파사드
├── websocket_manager.py        # 저수준 WebSocket 연결 관리
└── word_chain_manager.py       # 레거시 단어 체인 엔진 (Redis로 대체됨)
```

### 7. Configuration & Utils
```
config/
├── cookie.py               # 쿠키 설정
├── logging_config.py       # 로깅 설정
└── sentry_config.py        # Sentry 모니터링 설정 ✨ NEW

utils/
└── security.py             # 보안 유틸리티

db/
└── postgres.py             # PostgreSQL 연결 및 세션 관리
```

## 데이터 흐름

### 1. 일반 API 요청 흐름
```
Frontend Request
    ↓
Router (API Endpoint)
    ↓
Middleware (Auth/CORS/Rate Limiting)
    ↓
Service (Business Logic)
    ↓
Repository (Data Access)
    ↓
Model (SQLAlchemy ORM)
    ↓
PostgreSQL Database
```

### 2. 실시간 게임 데이터 흐름
```
Game Action
    ↓
WebSocket Router
    ↓
Redis Game Service
    ↓
Redis (Real-time State)
    ↓
WebSocket Broadcast
    ↓
All Connected Clients
```

### 3. 게임 결과 영속화 흐름
```
Game End (Redis)
    ↓
Game Data Persistence Service
    ↓
Game Log Repository
    ↓
PostgreSQL (Permanent Storage)
```

## 핵심 설계 패턴

### 1. 계층화 아키텍처 (Layered Architecture)
- **Router Layer**: HTTP 요청 처리 및 응답
- **Service Layer**: 비즈니스 로직 구현
- **Repository Layer**: 데이터 접근 로직
- **Model Layer**: 데이터 구조 정의

### 2. 의존성 주입 (Dependency Injection)
- FastAPI의 `Depends`를 활용한 의존성 관리
- 데이터베이스 세션, 서비스 인스턴스 주입
- 테스트 가능한 느슨한 결합 구조

### 3. 이중 아키텍처 패턴 (Dual Architecture)
- **PostgreSQL**: 영구 데이터 저장 (사용자, 게임 로그, 관계형 데이터)
- **Redis**: 실시간 게임 상태 (게임 진행, 타이머, 임시 데이터)

### 4. 미들웨어 패턴 (Middleware Pattern)
- 인증, CORS, 로깅, 보안 헤더 등을 미들웨어로 처리
- 관심사의 분리 및 재사용성 향상

## 보안 및 인증

### 세션 기반 인증 시스템
```
Login Request
    ↓
Auth Service (Session Token 생성)
    ↓
Secure HTTP-Only Cookie 설정
    ↓
Session Store (In-Memory + Auto Cleanup)
    ↓
Auth Middleware (요청마다 검증)
```

### 관리자 권한 시스템
```
Guest Model (is_admin 필드)
    ↓
Auth Middleware (get_admin_user)
    ↓
Router Dependencies (require_admin)
    ↓
Admin-only Endpoints
```

## 테스트 구조

### 테스트 아키텍처
```
tests/
├── conftest.py                    # 테스트 설정 및 픽스처
├── models/                        # 모델 테스트
│   ├── test_friendship_model.py   ✨ NEW
│   ├── test_game_mode_model.py    ✨ NEW
│   ├── test_item_model.py         ✨ NEW
│   └── test_player_profile_model.py ✨ NEW
├── repositories/                  # 리포지토리 테스트
│   ├── test_friendship_repository.py ✨ NEW
│   └── test_player_profile_repository.py ✨ NEW
└── services/                      # 서비스 테스트
    ├── test_friendship_service.py ✨ NEW
    ├── test_game_mode_service.py  ✨ NEW
    ├── test_item_service.py       ✨ NEW
    └── test_advanced_score_service.py ✨ NEW
```

## 성능 최적화

### 1. 데이터베이스 최적화
- 인덱스 설정 (guest_id, rank_points, 등)
- 커넥션 풀링
- 쿼리 최적화

### 2. 실시간 성능
- Redis를 통한 게임 상태 캐싱
- WebSocket 연결 관리
- 클라이언트 사이드 타이머 동기화

### 3. 메모리 관리
- 세션 자동 정리
- Redis TTL 설정 (24시간)
- 커넥션 풀 크기 조정

## 코드 품질 개선 사항

### ✨ 최근 개선사항
1. **데이터베이스 Base 클래스 통합**: 모든 모델이 일관된 Base 클래스 사용
2. **Redis 서비스 중복 제거**: v2 구현 및 관련 파일 정리
3. **포괄적인 테스트 커버리지**: 500+ 테스트 케이스 추가
4. **관리자 권한 시스템**: 완전한 관리자 기능 구현
5. **코드 정리**: 사용하지 않는 import 및 중복 코드 제거

### 📈 테스트 커버리지
- **Models**: 4개 새로운 모델 테스트 (74개 테스트 메서드)
- **Services**: 4개 새로운 서비스 테스트 (65개 테스트 메서드)
- **Repositories**: 2개 새로운 리포지토리 테스트 (38개 테스트 메서드)
- **총 추가**: 177개 테스트 메서드

## 향후 확장 계획

### 1. 마이크로서비스 분리 준비
- 서비스별 독립성 향상
- API Gateway 패턴 도입 고려

### 2. 캐싱 전략 강화
- Redis 클러스터링
- 다단계 캐싱 구조

### 3. 모니터링 및 관측성
- Sentry를 통한 에러 추적
- 성능 메트릭 수집
- 로그 분석 시스템