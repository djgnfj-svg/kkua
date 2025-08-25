# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**끄아 (KKUA) V2**는 실시간 멀티플레이어 한국어 끝말잇기 게임입니다. Pure WebSocket 아키텍처로 설계되어 실시간 통신, 아이템 시스템, 단어 검증, 게임 리포트 기능을 포함합니다.

## 기술 스택

### 백엔드
- **Python 3.11 + FastAPI** - 웹 프레임워크
- **WebSocket** - 실시간 통신
- **Redis** - 실시간 상태 관리 (게임 세션, 캐시)
- **PostgreSQL** - 영구 데이터 저장
- **SQLAlchemy** - ORM
- **JWT + bcrypt** - 인증/보안
- **pytest** - 테스트 프레임워크

### 프론트엔드
- **React 19** - UI 프레임워크
- **TypeScript** - 타입 안전성
- **Vite** - 빌드 도구
- **Zustand** - 상태 관리
- **TailwindCSS** - 스타일링
- **Native WebSocket** - 실시간 통신
- **Vitest** - 테스트 프레임워크

### 배포
- **Docker Compose** - 컨테이너 오케스트레이션

## 아키텍처 개요

### WebSocket 통신 아키텍처
- **JWT 인증**: WebSocket 연결 시 헤더에서 토큰 추출
- **연결 관리**: `connection_manager.py`에서 사용자별/룸별 연결 관리
- **메시지 라우팅**: `message_router.py`에서 메시지 타입별 핸들러 분기
- **게임 상태**: Redis를 통한 실시간 게임 상태 동기화

### 상태 관리 계층
1. **React Zustand Stores**: 클라이언트 UI 상태
2. **Redis Cache**: 실시간 게임 상태 (24시간 TTL)
3. **PostgreSQL**: 영구 데이터 (사용자, 게임 기록)

### 핵심 서비스 모듈
- **game_engine.py**: 게임 로직, 턴 관리, 승리 조건
- **word_validator.py**: 한국어 단어 검증 (10,794개 끄투 DB)
- **item_service.py**: 아이템 시스템 (5가지 희귀도)
- **score_calculator.py**: 점수 계산 알고리즘
- **timer_service.py**: 턴 제한 타이머 관리

## 개발 환경 실행

**Docker 개발 환경 (권장)**
```bash
# 전체 서비스 시작
docker-compose up -d --build

# 특정 서비스만 시작
docker-compose up -d db redis backend
docker-compose up -d frontend

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend

# 서비스 중지
docker-compose down
```

**로컬 개발 환경**
```bash
# 데이터베이스만 Docker로
docker-compose up -d db redis

# 백엔드 개발 서버
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 프론트엔드 개발 서버 
cd frontend
npm install
npm run dev
```

### 접속 정보
- **프론트엔드**: http://localhost:5173
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000
- **PostgreSQL**: localhost:5432 (postgres/password/kkua_db)
- **Redis**: localhost:6379

## 테스트 및 빌드 명령어

### 프론트엔드
```bash
# 린트 검사
npm run lint
# 또는 Docker에서
docker-compose exec frontend npm run lint

# 타입 체크
npx tsc -b  
# 또는 Docker에서
docker-compose exec frontend npx tsc -b

# 테스트 실행
npm run test
# 또는 Docker에서
docker-compose exec frontend npm run test

# 프로덕션 빌드
npm run build
# 또는 Docker에서
docker-compose exec frontend npm run build
```

### 백엔드
```bash
# 테스트 실행
python -m pytest tests/ -v
# 또는 Docker에서
docker exec kkua-backend-1 python -m pytest tests/ -v

# 테스트 커버리지
python -m pytest tests/ --cov=. --cov-report=term-missing
```

## 디버깅

### 로그 확인
```bash
# 실시간 로그 모니터링
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend

# Redis 모니터링
docker exec kkua-redis-1 redis-cli monitor

# 서비스 상태 확인
docker-compose ps
```

### 데이터베이스 접속
```bash
# PostgreSQL 접속
docker exec -it kkua-db-1 psql -U postgres -d kkua_db

# Redis 접속
docker exec -it kkua-redis-1 redis-cli

# Redis 캐시 초기화
docker exec kkua-redis-1 redis-cli FLUSHDB

# 단어 데이터 import
docker exec kkua-backend-1 python scripts/simple_kkutu_import.py
```

## 코딩 규칙

### 공통 규칙
- **타입 안전성**: TypeScript 엄격 모드, Python 타입 힌팅 필수
- **비동기 처리**: async/await 패턴 일관성 있게 사용
- **에러 처리**: 모든 예외 상황 적절히 처리
- **보안**: 사용자 입력 검증, JWT 토큰 검증, SQL injection 방지
- **성능**: 불필요한 리렌더링/DB 쿼리 방지

### 프론트엔드 (React + TypeScript)
- **함수형 컴포넌트**: React hooks 활용
- **상태 관리**: Zustand 스토어 패턴 (`stores/useGameStore.ts`, `stores/useUserStore.ts`)
- **스타일링**: TailwindCSS 유틸리티 클래스
- **WebSocket**: 커스텀 훅 `useWebSocket.ts` 활용
- **에러 처리**: ErrorBoundary 컴포넌트 사용

### 백엔드 (Python)
- **타입 힌팅**: 모든 함수에 타입 힌트 작성
- **로깅**: structlog를 통한 구조화된 로그
- **WebSocket**: `connection_manager.py`를 통한 연결 관리
- **게임 로직**: `services/` 모듈별로 책임 분리
- **데이터 모델**: SQLAlchemy ORM, Pydantic 검증

## 주요 파일 구조

### 백엔드 핵심 파일
- `main.py`: FastAPI 앱 진입점, CORS/인증 미들웨어
- `websocket/connection_manager.py`: WebSocket 연결 관리
- `websocket/message_router.py`: 메시지 타입별 라우팅
- `services/game_engine.py`: 게임 엔진 (턴 관리, 승리 조건)
- `redis_models.py`: Redis 게임 상태 모델

### 프론트엔드 핵심 파일  
- `src/stores/useGameStore.ts`: 게임 상태 관리
- `src/hooks/useWebSocket.ts`: WebSocket 연결 훅
- `src/components/ui/`: 재사용 UI 컴포넌트
- `src/pages/GameRoomPage.tsx`: 메인 게임 화면

## 현재 상태

**끄아(KKUA) V2 프로젝트 완성** ✅

### 완성된 기능
- ✅ 실시간 멀티플레이어 끝말잇기 게임
- ✅ JWT 인증 기반 WebSocket 통신
- ✅ 단어 카드 시스템 (난이도별 색상, 애니메이션)
- ✅ 플레이어 카드 UI (상태 표시, 점수 관리)
- ✅ 아이템 시스템 (5가지 희귀도)
- ✅ 게임 리포트 및 순위 시스템
- ✅ 반응형 모바일 디자인
- ✅ 자동 재연결 로직
- ✅ Docker 컨테이너 환경
* **실시간 게임 서버 구현** - WebSocket + asyncio로 6명 동시 플레이, 50ms 미만 응답으로 실시간성 확보
* **데이터베이스 성능 개선** - Redis 캐싱 도입으로 단어 검증 80% 빨라짐, DB 쿼리 85% 감소 달성
* **사용자 인증 구현** - JWT 기반 WebSocket 보안 연결, 토큰 자동 갱신으로 끊김 없는 플레이 지원
* **안정성 강화** - Rate Limiting(분당 60회)과 자동 재연결로 100명 동시 접속 안정적 처리
* **배포 자동화 구축** - Docker + GitHub Actions CI/CD로 수동 배포 제로화, 배포 시간 10분 → 3분 단축