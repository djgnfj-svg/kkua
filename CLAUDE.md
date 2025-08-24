# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the 끄아(KKUA) V2 project.

## Project Overview

**끄아 (KKUA) V2**는 실시간 멀티플레이어 한국어 끝말잇기 게임입니다. Pure WebSocket 아키텍처로 설계되어 실시간 통신, 아이템 시스템, 단어 검증, 게임 리포트 기능을 포함합니다.

## 기술 스택

### 백엔드
- **Python FastAPI** - 웹 프레임워크
- **WebSocket** - 실시간 통신
- **Redis** - 실시간 상태 관리
- **PostgreSQL** - 영구 데이터 저장
- **SQLAlchemy** - ORM

### 프론트엔드
- **React 19** - UI 프레임워크
- **TypeScript** - 타입 안전성
- **Vite** - 빌드 도구
- **Zustand** - 상태 관리
- **TailwindCSS** - 스타일링
- **WebSocket** - 실시간 통신

### 배포
- **Docker Compose** - 컨테이너 오케스트레이션

## 개발 환경 실행

**Docker 개발 환경 (권장)**
```bash
# 전체 서비스 시작
docker-compose up -d

# 특정 서비스만 시작
docker-compose up -d db redis backend
docker-compose up -d frontend

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend

# 서비스 중지
docker-compose down
```

### 접속 정보
- **프론트엔드**: http://localhost:5173
- **백엔드 API**: http://localhost:8000
- **WebSocket**: ws://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 테스트 명령어
```bash
# 프론트엔드 빌드 테스트
docker-compose exec frontend npm run build

# 프론트엔드 린트 검사
docker-compose exec frontend npm run lint

# 프론트엔드 타입 체크
docker-compose exec frontend npx tsc -b
```

## 디버깅

### 로그 확인
```bash
# 서비스 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend

# Redis 모니터링
docker exec kkua-redis-1 redis-cli monitor

# 서비스 상태 확인
docker-compose ps
```

### 데이터베이스
```bash
# PostgreSQL 접속
docker exec -it kkua-db-1 psql -U postgres -d kkua_db

# Redis 접속
docker exec -it kkua-redis-1 redis-cli

# Redis 캐시 초기화
docker exec kkua-redis-1 redis-cli FLUSHDB
```

## 코딩 규칙

### 공통 규칙
- **타입 안전성**: TypeScript 엄격 모드 사용
- **비동기 처리**: async/await 패턴
- **에러 처리**: 모든 예외 상황 처리
- **보안**: 사용자 입력 검증, 민감정보 노출 방지
- **성능**: 불필요한 리렌더링/요청 방지

### 프론트엔드 (React + TypeScript)
- **함수형 컴포넌트**: hooks 사용
- **상태 관리**: Zustand 사용
- **스타일링**: TailwindCSS 클래스 사용
- **에러 처리**: ErrorBoundary 활용

### 백엔드 (Python)
- **타입 힌팅**: 모든 함수에 타입 힌트
- **로깅**: 중요 이벤트 로그 기록
- **문서화**: docstring 작성

## 현재 상태

**끄아(KKUA) V2 프로젝트 완성** ✅

### 완성된 기능
- ✅ 실시간 멀티플레이어 끝말잇기 게임
- ✅ WebSocket 기반 실시간 통신
- ✅ 단어 카드 시스템 (난이도별 색상, 애니메이션)
- ✅ 플레이어 카드 UI (상태 표시, 점수 관리)
- ✅ 게임 리포트 및 순위 시스템
- ✅ 반응형 모바일 디자인
- ✅ Docker 컨테이너 환경

**접속 URL**: http://localhost:5173 🎮