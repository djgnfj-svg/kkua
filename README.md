# 끄아 (KKUA) V2 🎮

**실시간 멀티플레이어 한국어 끝말잇기 게임**

Pure WebSocket 아키텍처로 재설계된 차세대 끝말잇기 게임입니다. 실제 끄투(KKuTu) 단어 데이터베이스를 활용하여 10,794개의 한국어 단어로 플레이할 수 있습니다.

## ✨ 주요 기능

- 🎯 **실시간 멀티플레이어** - 최대 6명까지 동시 플레이
- 📚 **실제 끄투 단어 DB** - 10,794개 한국어 단어 지원
- 🎮 **아이템 시스템** - 5가지 희귀도의 전략적 아이템
- ⏱️ **실시간 타이머** - 30초 턴 제한, 아이템으로 조절 가능
- 📊 **게임 리포트** - 상세한 게임 통계 및 순위
- 💬 **실시간 채팅** - 게임 중 소통 기능
- 📱 **모바일 반응형** - 모든 디바이스에서 최적화된 경험
- 🔄 **자동 재연결** - 네트워크 끊김 시 자동 복구

## 🚀 빠른 배포

**로컬 배포 (권장)**
```bash
./quick-deploy.sh
```

**AWS EC2 원클릭 배포**
```bash
curl -o ec2-install.sh https://raw.githubusercontent.com/djgnfj-svg/kkua/develop/ec2-install.sh && chmod +x ec2-install.sh && ./ec2-install.sh
```

**자동으로 처리되는 것들:**
- ✅ Docker & Docker Compose 설치
- ✅ GitHub에서 프로젝트 클론 (Personal Access Token 지원)
- ✅ 환경변수 자동 설정 (EC2 Public IP 감지)
- ✅ 데이터베이스 초기화 (실제 끄투 단어 포함)
- ✅ 서비스 시작 및 상태 확인

**📋 EC2 인스턴스 요구사항:**
- **AMI**: Ubuntu Server 22.04 LTS
- **타입**: t3.small 권장 (t3.micro 최소)
- **스토리지**: 20GB
- **보안 그룹**: 포트 80, 443 오픈

자세한 배포 가이드: [docs/EC2_DEPLOY_GUIDE.md](./docs/EC2_DEPLOY_GUIDE.md)

## 💻 로컬 개발 환경

### 빠른 시작
```bash
# 저장소 클론
git clone https://github.com/djgnfj-svg/kkua.git
cd kkua

# Docker Compose로 전체 서비스 시작
docker-compose up -d --build

# 또는 개발 환경 (데이터베이스만 Docker)
docker-compose up -d db redis

# 백엔드 개발 서버 (터미널 1)
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 프론트엔드 개발 서버 (터미널 2)
cd frontend
npm install
npm run dev
```

### 서비스 접속
- 🎮 **게임**: http://localhost:5173
- 📚 **API 문서**: http://localhost:8000/docs
- ❤️ **헬스체크**: http://localhost:8000/health

## 🏗️ 기술 스택

### 백엔드
- **Python 3.11** + **FastAPI** - 고성능 웹 프레임워크
- **PostgreSQL** - 영구 데이터 저장 (게임 기록, 사용자 정보)
- **Redis** - 실시간 게임 상태 관리 (24시간 TTL)
- **WebSocket** - 실시간 양방향 통신
- **SQLAlchemy** - ORM 및 데이터베이스 마이그레이션
- **Pydantic** - 데이터 검증 및 직렬화

### 프론트엔드
- **React 19** + **TypeScript** - 현대적 UI 라이브러리
- **Vite** - 빠른 빌드 도구
- **Zustand** - 경량 상태 관리
- **TailwindCSS** - 유틸리티 기반 스타일링
- **React Router** - SPA 라우팅
- **Native WebSocket** - 실시간 통신

### 인프라 & 배포
- **Docker** + **Docker Compose** - 컨테이너화
- **nginx** - 리버스 프록시 (프로덕션)
- **AWS EC2** - 클라우드 배포
- **GitHub Actions** - CI/CD (선택사항)

## 🎯 게임 시스템

### 아이템 시스템
- **⭐ 일반** (70%): 시간 연장, 기본 힌트
- **🔸 희귀** (20%): 점수 배수, 상대 방해  
- **💎 에픽** (7%): 완벽한 힌트, 보호막
- **🌟 전설** (2.5%): 연쇄 점수, 시간 정지
- **👑 신화** (0.5%): 궁극기 효과

### 게임 모드
- **일반 모드**: 기본 끝말잇기
- **속도전**: 15초 제한 빠른 게임
- **아이템전**: 아이템 효과 2배
- **단어 길이 제한**: 3글자 이상, 5글자 이하 등
- **주제별**: 특정 카테고리 단어만

### 점수 시스템
- **기본 점수**: 단어 길이 × 10
- **난이도 보너스**: 어려운 단어 추가 점수
- **연속 보너스**: 연속 성공 시 배수 적용
- **아이템 보너스**: 아이템 효과로 점수 증가

## 📊 성능 최적화

- **Connection Pool**: DB 연결 효율성
- **Redis Caching**: 자주 사용하는 데이터 캐싱
- **WebSocket Optimization**: 메시지 압축 및 배치 처리
- **React Optimization**: useMemo, useCallback 활용
- **Mobile Optimization**: 터치 이벤트 최적화

## 🛡️ 보안 & 안정성

- **JWT 인증**: 토큰 기반 사용자 인증
- **Rate Limiting**: API 호출 제한
- **Input Validation**: 모든 사용자 입력 검증
- **CORS 설정**: 허용된 도메인만 접근
- **SQL Injection 방지**: SQLAlchemy ORM 사용
- **WebSocket 보안**: 연결 수 제한 및 검증

## 📋 개발 가이드

### 프로젝트 구조
```
kkua/
├── backend/           # FastAPI 백엔드
│   ├── models/       # SQLAlchemy 모델
│   ├── services/     # 비즈니스 로직
│   ├── websocket/    # WebSocket 핸들러
│   └── scripts/      # 초기화 스크립트
├── frontend/         # React 프론트엔드  
│   ├── src/pages/    # 페이지 컴포넌트
│   ├── src/components/ # UI 컴포넌트
│   ├── src/stores/   # Zustand 스토어
│   └── src/hooks/    # 커스텀 훅
├── docs/             # 프로젝트 문서
├── ec2-install.sh    # EC2 간단 설치 스크립트
├── quick-deploy.sh   # 로컬 배포 스크립트
└── CLAUDE.md         # 개발 가이드
```

### 주요 명령어
```bash
# 테스트 실행
cd backend && python -m pytest tests/ -v
cd frontend && npm run test

# 린트 및 타입 체크
cd frontend && npm run lint
cd frontend && npx tsc -b

# 프로덕션 빌드
docker-compose up -d --build
cd frontend && npm run build

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 🚨 문제 해결

### 자주 발생하는 문제들

**1. WebSocket 연결 실패**
```bash
# JWT 토큰 확인
curl http://localhost:8000/health
# Redis 연결 확인  
docker-compose logs redis
```

**2. 데이터베이스 연결 실패**
```bash
# PostgreSQL 컨테이너 상태 확인
docker-compose ps db
# 데이터베이스 연결 테스트
docker exec -it kkua-db-1 psql -U postgres -d kkua_db
```

**3. 단어 데이터 없음**
```bash
# 단어 데이터 import 실행
docker exec kkua-backend-1 python scripts/simple_kkutu_import.py
```

**4. 메모리 부족 (EC2)**
```bash
# 스왑 메모리 확인
free -h
# 스왑 추가 (2GB)
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
```

## 📈 모니터링

### 시스템 상태 확인
```bash
# 서비스 상태
docker-compose ps

# 리소스 사용량
htop
docker stats

# 디스크 사용량
df -h
docker system df
```

### 로그 모니터링
```bash
# 실시간 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs backend --tail=100
docker-compose logs frontend --tail=100
```

## 🤝 기여하기

1. **Fork** 이 저장소
2. **Feature branch** 생성 (`git checkout -b feature/amazing-feature`)
3. **변경사항 커밋** (`git commit -m 'Add amazing feature'`)
4. **Branch에 Push** (`git push origin feature/amazing-feature`)
5. **Pull Request** 생성

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.

## 👥 팀 구성

**Backend**: [송영재](https://github.com/djgnfj-svg)  
**Frontend**: [박형석](https://github.com/b-hyoung), [이승연](https://github.com/SeungYeon04)

## 🔗 참고 자료

- **개발 가이드**: [CLAUDE.md](./CLAUDE.md)
- **배포 가이드**: [docs/EC2_DEPLOY_GUIDE.md](./docs/EC2_DEPLOY_GUIDE.md)
- **API 문서**: http://localhost:8000/docs (서버 실행 후)
- **끄투 원본**: https://github.com/JJoriping/KKuTu

---

**🎮 지금 바로 플레이해보세요!**

```bash
curl -o ec2-install.sh https://raw.githubusercontent.com/djgnfj-svg/kkua/develop/ec2-install.sh && chmod +x ec2-install.sh && ./ec2-install.sh
```

**Happy Gaming! 끝말잇기의 재미를 경험해보세요! 🎉**