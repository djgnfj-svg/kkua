# KKUA 프로젝트 문서

## 문서 구조

- [아키텍처 개요](./architecture.md) - 전체 시스템 아키텍처와 설계 패턴
- [WebSocket 로직](./websocket.md) - 실시간 통신 상세 구현
- [API 문서](./api.md) - REST API 엔드포인트 가이드
- [데이터베이스 스키마](./database.md) - 데이터 모델 및 관계
- [인증 시스템](./authentication.md) - 세션 기반 인증 구현
- [게임 로직](./game-logic.md) - 끝말잇기 게임 규칙과 구현
- [개발 가이드](./development.md) - 개발 환경 설정 및 워크플로우
- [배포 가이드](./deployment.md) - 프로덕션 배포 방법

## 프로젝트 개요

**끄아 (KKUA)**는 실시간 멀티플레이어 끝말잇기 게임입니다.

### 핵심 기술 스택
- **Backend**: FastAPI + PostgreSQL + SQLAlchemy
- **Frontend**: React + TailwindCSS + Zustand
- **Real-time**: WebSocket 기반 실시간 통신
- **Authentication**: 세션 기반 인증 (HTTP-only cookies)
- **Deployment**: Docker + Nginx

### 주요 기능
- 실시간 멀티플레이어 게임
- 방 생성 및 참가 시스템
- 채팅 및 상태 동기화
- 게임 결과 통계
- 반응형 UI

### 최근 업데이트
- 코드베이스 대규모 정리 및 최적화
- WebSocket 아키텍처 리팩토링
- 게임 결과 데이터베이스 통합
- 버그 수정 및 안정성 개선