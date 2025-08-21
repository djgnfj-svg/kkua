# 끄아 (KKUA)

실시간 멀티플레이어 끝말잇기 게임

## 🚀 빠른 시작

```bash
# 저장소 클론
git clone <repository-url>
cd kkua

# 데이터베이스 시작
docker-compose up -d db redis

# 백엔드 시작 (터미널 1)
cd backend
python -m uvicorn main:app --reload

# 프론트엔드 시작 (터미널 2)
cd frontend
npm run dev

# 서비스 확인
# 프론트엔드: http://localhost:5173
# 백엔드: http://localhost:8000
```

## 💻 개발 환경

### 요구사항
- Docker
- Docker Compose

### 주요 명령어
```bash
# 데이터베이스만 시작
docker-compose up -d db redis

# 백엔드 개발 서버
cd backend && python -m uvicorn main:app --reload

# 프론트엔드 개발 서버
cd frontend && npm run dev

# 빌드 테스트
npm run build
```

## 🏗 기술 스택

**Backend**
- FastAPI
- PostgreSQL
- Redis
- WebSocket

**Frontend**
- React
- TailwindCSS
- Zustand

**인프라**
- Docker
- Docker Compose

## 📋 주요 기능

- 실시간 멀티플레이어 끝말잇기
- 게스트 기반 간편 로그인
- WebSocket 실시간 통신
- 게임 룸 생성 및 참가
- 게임 결과 및 통계

## 👥 팀 구성

**Backend**: [송영재](https://github.com/djgnfj-svg)
**Frontend**: [박형석](https://github.com/b-hyoung), [이승연](https://github.com/SeungYeon04)

---

더 자세한 정보는 [CLAUDE.md](./CLAUDE.md)를 참고하세요.