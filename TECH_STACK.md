# 🚀 끄아(KKUA) 기술 스택

## 📋 개요
실시간 멀티플레이어 한국어 끝말잇기 게임

## 🛠️ 핵심 기술

### Backend
- **FastAPI** - 고성능 비동기 웹 프레임워크
- **PostgreSQL** - 영구 데이터 저장 (사용자, 게임 로그)
- **Redis** - 실시간 게임 상태 관리 (24시간 TTL)
- **WebSocket** - 실시간 양방향 통신
- **SQLAlchemy** - ORM 및 데이터베이스 관리
- **Pydantic** - 데이터 검증 및 직렬화
- **Uvicorn** - ASGI 서버

### Frontend
- **React** - UI 라이브러리
- **Zustand** - 상태 관리
- **TailwindCSS** - 유틸리티 기반 스타일링
- **Axios** - HTTP 클라이언트
- **React Router** - 라우팅

### DevOps & Infrastructure
- **Docker & Docker Compose** - 컨테이너화 및 오케스트레이션
- **Nginx** - 리버스 프록시 (프로덕션)
- **GitHub Actions** - CI/CD 파이프라인

## 🏗️ 아키텍처 패턴

### 1. 듀얼 데이터베이스 아키텍처
- **PostgreSQL**: 영구 데이터 (계정, 로그, 통계)
- **Redis**: 실시간 게임 상태, 타이머, 캐싱

### 2. 레이어드 아키텍처
```
Routers → Services → Repositories → Models
```

### 3. 실시간 통신
- WebSocket + 지수 백오프 재연결
- 선택적 브로드캐스팅 (중요 시점만)
- 클라이언트 타이머 동기화

## 🔐 보안 & 인증

### 세션 기반 인증
- HTTP-only 쿠키
- 세션 토큰 (24시간 만료)
- CSRF 보호
- 미들웨어 검증

### 보안 헤더
- CORS 설정
- XSS 방지
- HSTS (프로덕션)
- Rate Limiting

## ⚡ 성능 최적화

### Redis 트랜잭션
- 단어 제출 원자성 보장
- 경쟁 조건 방지

### 스마트 브로드캐스팅
- 타이머: 10, 5, 3, 2, 1초만 전송
- 이벤트 기반 업데이트

### 연결 관리
- Redis 연결 풀링
- WebSocket 연결 매니저
- 자동 세션 정리

## 🎮 게임 기능

### 핵심 시스템
- **실시간 끝말잇기** - 한국어 단어 검증
- **타이머 시스템** - 턴당 30초 제한
- **점수 시스템** - 단어 길이, 속도, 콤보
- **라운드 시스템** - 최대 10라운드

### 고급 기능
- **게임 모드** - 클래식, 스피드, 아이템
- **아이템 시스템** - 전략적 게임플레이
- **친구 시스템** - 소셜 기능
- **통계 추적** - 상세 게임 분석

## 📦 주요 라이브러리

### Backend
```
fastapi==0.104.1
redis==5.0.1
sqlalchemy==2.0.23
pydantic==2.5.2
python-jose==3.3.0
pytest==7.4.3
```

### Frontend
```
react@18.2.0
zustand@4.4.7
tailwindcss@3.3.6
axios@1.6.2
react-router-dom@6.20.1
```

## 🚀 배포

### 개발 환경
```bash
./deploy.sh
```

### 프로덕션 환경
```bash
./deploy.sh production
```

### 컨테이너 구성
- `backend` - FastAPI 앱
- `frontend` - React 앱 (개발)
- `db` - PostgreSQL
- `redis` - Redis
- `nginx` - 리버스 프록시 (프로덕션)

## 📊 모니터링

- **로깅** - 멀티 레벨 로그 (앱, 에러, 감사, 성능)
- **헬스체크** - 모든 서비스 상태 확인
- **메트릭** - 응답 시간, 처리량 추적

## 🧪 테스팅

- **Backend** - pytest (70%+ 커버리지)
- **Frontend** - Jest & React Testing Library
- **CI/CD** - GitHub Actions 자동 테스트

---

**팀 구성**
- Backend: [송영재](https://github.com/djgnfj-svg)
- Frontend: [박형석](https://github.com/b-hyoung), [이승연](https://github.com/SeungYeon04)