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
- **React 19** - UI 프레임워크
- **TypeScript** - 타입 안전성
- **Vite** - 빌드 도구
- **Zustand** - 상태 관리
- **WebSocket** - 실시간 통신
- **TailwindCSS** - 스타일링
- **React Router** - 라우팅

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
├── auth.py                          # JWT 인증 로직
├── database.py                      # 데이터베이스 설정
├── redis_models.py                  # Redis 모델
├── requirements.txt                 # Python 의존성
├── Dockerfile                       # Docker 설정
├── database_schema.sql              # 데이터베이스 스키마
├── models/                         # SQLAlchemy 모델
│   ├── __init__.py
│   ├── base.py
│   ├── user_models.py
│   ├── game_models.py
│   ├── item_models.py
│   ├── log_models.py
│   └── dictionary_models.py
├── scripts/                        # 초기화 스크립트
│   ├── __init__.py
│   ├── init_data.py
│   ├── extended_words.py
│   └── healthcheck.py
├── services/                       # 비즈니스 로직
│   ├── __init__.py
│   ├── game_engine.py
│   ├── word_validator.py
│   ├── item_service.py
│   ├── timer_service.py
│   ├── score_calculator.py
│   ├── analytics_service.py
│   ├── cache_service.py
│   └── game_mode_service.py
└── websocket/                      # WebSocket 관련
    ├── __init__.py
    ├── connection_manager.py
    ├── message_router.py
    ├── game_handler.py
    └── websocket_endpoint.py
```

### 프론트엔드 구조 (TypeScript + Vite)
```
frontend/
├── public/
│   └── vite.svg
├── src/
│   ├── components/
│   │   ├── ChatPanel.tsx
│   │   ├── CreateRoomModal.tsx
│   │   ├── GameReport.tsx
│   │   ├── GameRoomList.tsx
│   │   ├── ItemPanel.tsx
│   │   ├── LoginForm.tsx
│   │   ├── Toast.tsx
│   │   └── ui/
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── ErrorBoundary.tsx
│   │       ├── Input.tsx
│   │       ├── Loading.tsx
│   │       ├── Modal.tsx
│   │       └── Skeleton.tsx
│   ├── hooks/
│   │   ├── useNativeWebSocket.ts
│   │   ├── useNavigationProtection.ts
│   │   ├── usePersistedState.ts
│   │   └── useWebSocket.ts
│   ├── pages/
│   │   ├── GameRoomPage.tsx
│   │   ├── LobbyPage.tsx
│   │   └── LoginPage.tsx
│   ├── stores/
│   │   ├── useGameStore.ts
│   │   ├── useUiStore.ts
│   │   └── useUserStore.ts
│   ├── types/
│   │   └── game.ts
│   ├── utils/
│   │   ├── api.ts
│   │   └── tabCommunication.ts
│   ├── App.tsx
│   ├── Router.tsx
│   └── main.tsx
├── package.json
├── vite.config.ts
├── tsconfig.json
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
# 프로젝트 클론
git clone https://github.com/YOUR_USERNAME/kkua.git
cd kkua

# 프론트엔드 의존성 설치
cd frontend
npm install
```

### ⚠️ 개발 환경 옵션

#### Option 1: Docker 개발 환경 (권장)
```bash
# 전체 서비스 시작 (백엔드 + 프론트엔드 + DB + Redis)
docker-compose up -d --build

# 백엔드만 시작 (데이터베이스 포함)
docker-compose up -d backend db redis

# 프론트엔드만 시작
docker-compose up -d frontend

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend

# 서비스 중지
docker-compose down
```

#### Option 2: 혼합 개발 환경 (빠른 개발)
```bash
# 데이터베이스만 Docker로 시작
docker-compose up -d db redis

# 백엔드 로컬 실행 (터미널 1)
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 프론트엔드 로컬 실행 (터미널 2) 
cd frontend
npm run dev
```

**참고:** README.md의 빠른 시작 가이드는 혼합 환경을 사용하므로 상황에 따라 선택

### EC2 원클릭 배포
```bash
# AWS EC2에서 전체 서비스 자동 배포
curl -o deploy.sh https://raw.githubusercontent.com/YOUR_USERNAME/kkua/develop/deploy.sh && chmod +x deploy.sh && ./deploy.sh

# 프로덕션 환경 시작 (로컬에서)
docker-compose -f docker-compose.prod.yml up -d --build

# 시크릿 키 생성
./generate-secrets.sh

# 로그 확인 (프로덕션)
docker-compose -f docker-compose.prod.yml logs -f
```

**배포 가이드 참고:**
- `EC2_DEPLOY.md` - AWS EC2 원클릭 배포 가이드
- `README.md` - 전체 프로젝트 개요 및 빠른 시작 가이드

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

### 테스트 및 빌드
```bash
# 백엔드 테스트
cd backend
python -m pytest tests/ -v

# 프론트엔드 테스트
cd frontend
npm run test

# 프론트엔드 테스트 (UI 모드)
cd frontend
npm run test:ui

# 프론트엔드 린트 검사
cd frontend
npm run lint

# 프론트엔드 타입 체크
cd frontend
npx tsc -b

# 프론트엔드 빌드 테스트
cd frontend
npm run build

# 프론트엔드 개발 서버 시작
cd frontend
npm run dev

# 프론트엔드 프리뷰 (빌드 결과)
cd frontend  
npm run preview
```

## 코딩 규칙

### 백엔드 (Python)
- **타입 힌팅 필수**: 모든 함수에 타입 힌트 추가
- **비동기 처리**: async/await 사용
- **에러 처리**: 모든 예외 상황 처리
- **로깅**: 중요 이벤트 로그 기록
- **문서화**: docstring 작성

### 프론트엔드 (React + TypeScript)
- **함수형 컴포넌트**: hooks 사용
- **타입 안전성**: TypeScript 엄격 모드
- **상태 관리**: Zustand 사용
- **스타일링**: TailwindCSS 클래스 사용
- **에러 처리**: ErrorBoundary 활용
- **라우팅**: React Router 사용
- **빌드 도구**: Vite 사용

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
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 프론트엔드 (Vite)
```bash
# API 연결
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_DEBUG=true

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
5. **단어 데이터 없음**: 단어 import 스크립트 실행
6. **메모리 부족 (EC2)**: 스왑 메모리 설정 확인

### 로그 확인
```bash
# 백엔드 로그
docker-compose logs -f backend

# Redis 명령어 모니터링
docker exec kkua-redis-1 redis-cli monitor

# 데이터베이스 쿼리 로그
# PostgreSQL 설정에서 log_statement = 'all' 활성화

# 컨테이너 상태 확인
docker-compose ps

# 시스템 리소스 확인
htop
docker stats

# 단어 데이터 import (필요시)
docker exec kkua-backend-1 python scripts/init_data.py
```

### 서비스 관리
```bash
# 서비스 상태 확인
docker-compose ps

# 서비스 재시작
docker-compose restart backend
docker-compose restart frontend

# 서비스 완전 재빌드
docker-compose up -d --build --force-recreate

# 컨테이너 정리
docker-compose down --volumes --remove-orphans
docker system prune -f

# 백엔드 개발 모드 (핫 리로드)
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 프론트엔드 개발 모드 (핫 리로드) 
cd frontend
npm run dev
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

현재 상태: **프론트엔드 완성 및 전체 시스템 완료** (2025-08-23)

**🎉 완료된 작업들:**

### **Phase 1-6: 백엔드 시스템** ✅
✅ 데이터베이스 스키마 및 SQLAlchemy 모델
✅ Redis 실시간 상태 관리 시스템
✅ WebSocket 인프라 및 연결 관리
✅ 게임 엔진 및 핵심 서비스 (단어 검증, 타이머, 점수 계산)
✅ 아이템 시스템 (10가지 아이템, 희귀도별 드롭 시스템)
✅ 다중 게임 모드 (7가지 모드, 팀 배틀, 관전 모드)
✅ 고급 기능 (캐싱, 분석, 모니터링)
✅ 테스트 및 배포 시스템

### **Phase 7: 프론트엔드 구현** ✅ (2025-08-20 완료)
✅ React + Zustand 기반 상태 관리
✅ WebSocket 실시간 통신 구현
✅ 완전한 게임 UI/UX (게임보드, 플레이어 목록, 타이머)
✅ 게임 리포트 시스템 (최종 순위, 플레이어 통계)
✅ 아이템 인벤토리 UI (쿨다운, 희귀도별 스타일링)
✅ 실시간 채팅 시스템 (타입별 메시지, 자동 스크롤)
✅ 모바일 반응형 디자인 최적화
✅ 로딩 스켈레톤 및 에러 바운더리
✅ 게임 시작 조건 개선 (최소 2명 인원 체크)

**🚀 시스템 상태:**
- **백엔드**: 완전 구현 및 테스트 완료
- **프론트엔드**: 완전 구현 및 빌드 성공
- **통합**: API 연결 및 실시간 통신 검증 완료
- **배포**: Docker Compose 환경 구성 완료

**💡 향후 개선 가능한 영역:**
1. **성능 최적화**: 대용량 트래픽 대응
2. **모니터링 강화**: 실시간 대시보드 추가
3. **추가 게임 모드**: 새로운 게임 변형 개발
4. **모바일 앱**: React Native 포팅 고려

끄아(KKUA) V2 프로젝트가 완성되었습니다! 🎮✨