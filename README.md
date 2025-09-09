# 🎮 끄아(KKUA) - 실시간 멀티플레이어 한국어 끝말잇기 게임

**WebSocket 기반 실시간 멀티플레이어 한국어 끝말잇기 게임**

## 🚀 주요 기능

- **실시간 멀티플레이어**: WebSocket을 통한 지연 없는 실시간 게임
- **대용량 사전 데이터**: 357,644개 한국어 단어 지원
- **JWT 인증**: 보안성을 갖춘 사용자 인증 시스템
- **Redis 캐싱**: 고성능 실시간 상태 관리
- **두음법칙 지원**: 한국어 언어학적 특성 반영

## 🛠 기술 스택

### Backend
- **FastAPI** + **WebSocket** - 실시간 통신
- **PostgreSQL** - 영구 데이터 저장
- **Redis** - 캐싱 및 세션 관리
- **JWT** + **bcrypt** - 인증/보안

### Frontend
- **React 19** + **TypeScript** - 타입 안전성
- **Zustand** - 상태 관리
- **TailwindCSS** - 반응형 디자인

### Infrastructure
- **Docker Compose** - 컨테이너 오케스트레이션
- **Nginx** - 리버스 프록시

## ⚡ 빠른 시작

### 개발 환경
```bash
./dev.sh
# 게임: http://localhost:5173
# API: http://localhost:8000/docs
```

### 프로덕션 배포
```bash
./prod.sh [도메인명]
```

## 📊 성능 특징

- **실시간 처리**: WebSocket 기반 지연 없는 통신
- **대용량 최적화**: 36만개 단어 DB 고속 검색
- **메모리 효율**: Redis TTL 기반 세션 관리
- **확장성**: Docker 컨테이너 기반 배포

## 🏗 아키텍처

```
Frontend (React) ←→ Nginx ←→ FastAPI Backend
                              ↓
                          PostgreSQL + Redis
```

- **3-tier 아키텍처**: 프레젠테이션, 비즈니스, 데이터 레이어 분리
- **이중화 데이터베이스**: PostgreSQL(영구) + Redis(캐시)
- **WebSocket 연결 관리**: JWT 기반 인증된 실시간 연결

## 📝 개발자 노트

이 프로젝트는 백엔드 개발 역량 향상을 위해 개발되었으며, 실시간 통신, 성능 최적화, 확장 가능한 아키텍처 설계에 중점을 두었습니다.