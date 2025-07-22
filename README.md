# 끄아 (KKUA)

실시간 멀티플레이어 끝말잇기 게임

## 🚀 빠른 시작

```bash
# 저장소 클론
git clone <repository-url>
cd kkua

# 환경 설정
cp backend/.env.example backend/.env

# Docker 배포 (원클릭)
./deploy.sh

# 서비스 확인
# 프론트엔드: http://localhost:3000
# 백엔드: http://localhost:8000
# API 문서: http://localhost:8000/docs
```

## 💻 개발 환경

### 요구사항
- Docker
- Docker Compose

### 주요 명령어
```bash
# 서비스 시작
./deploy.sh

# 서비스 중지  
./stop.sh

# 로그 확인
docker-compose logs -f

# 테스트 실행
docker-compose run --rm backend-test
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
- 아이템 시스템이 있는 게임플레이
- 세션 기반 인증
- 실시간 채팅
- 게임 통계 및 결과

## 👥 팀 구성

**Backend**: [송영재](https://github.com/djgnfj-svg)
**Frontend**: [박형석](https://github.com/b-hyoung), [이승연](https://github.com/SeungYeon04)

---

더 자세한 배포 정보는 [DEPLOYMENT.md](./DEPLOYMENT.md)를 참고하세요.