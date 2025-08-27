# 프로젝트 구조

## 📁 디렉터리 구조

```
kkua/
├── 🔧 config/                    # 설정 파일들
│   └── nginx.prod.conf           # Nginx 리버스 프록시 설정
│
├── 📜 scripts/                   # 배포 및 유틸리티 스크립트
│   ├── dev-start.sh             # 개발 환경 시작
│   ├── quick-deploy.sh          # 로컬/서버 배포
│   ├── prod-deploy.sh           # 프로덕션 배포 (quick-deploy.sh 래퍼)
│   └── ec2-install.sh           # AWS EC2 원클릭 설치
│
├── 🏗️  backend/                  # Python FastAPI 백엔드
│   ├── models/                  # SQLAlchemy 데이터베이스 모델
│   ├── services/                # 비즈니스 로직 서비스들
│   ├── websocket/               # WebSocket 연결 및 메시지 처리
│   ├── scripts/                 # 백엔드 유틸리티 스크립트
│   └── database/                # 데이터베이스 관련 파일들
│       └── data/                # 초기 데이터 (한국어 단어 CSV)
│
├── 🎨 frontend/                  # React + TypeScript 프론트엔드
│   ├── src/
│   │   ├── components/          # React 컴포넌트들
│   │   ├── pages/               # 페이지 컴포넌트들  
│   │   ├── hooks/               # 커스텀 React 훅
│   │   ├── stores/              # Zustand 상태 관리
│   │   └── utils/               # 유틸리티 함수들
│   ├── Dockerfile.dev           # 개발용 Docker 설정
│   ├── Dockerfile.prod          # 프로덕션용 Docker 설정
│   └── nginx.conf              # 프론트엔드 Nginx 설정
│
├── 📋 docs/                     # 프로젝트 문서들
├── 🗄️  database/                # 데이터베이스 초기 데이터
│   └── data/
│       └── korean_words.csv    # 한국어 단어 데이터 (35만+ 단어)
│
├── docker-compose.yml          # 통합 Docker Compose 설정 (환경변수로 모드 전환)
├── .env.dev                  # 개발 환경 변수
├── .env.prod                 # 프로덕션 환경 변수  
├── .env.example               # 환경변수 예제 파일
├── CLAUDE.md                 # Claude Code 개발 가이드
├── README.md                 # 프로젝트 개요 및 사용법
└── PROJECT_STRUCTURE.md     # 이 파일
```

## 🎯 파일별 용도

### Docker 환경 설정
- `docker-compose.yml` - **통합 설정** (환경변수로 개발/프로덕션 모드 전환)
- `.env.dev` - 개발 환경 변수 (볼륨 마운트, 개발 모드)
- `.env.prod` - 프로덕션 환경 변수 (Nginx 포함, 멀티워커, 재시작 정책)

### 배포 스크립트
- `scripts/dev-start.sh` - 개발 환경 빠른 시작
- `scripts/quick-deploy.sh` - 로컬/서버 프로덕션 배포  
- `scripts/ec2-install.sh` - AWS EC2 자동 설치 스크립트

### 설정 파일
- `config/nginx.prod.conf` - 프로덕션용 Nginx 리버스 프록시 설정
- `.env.example` - 환경변수 템플릿

## 🚀 사용법

### 개발할 때
```bash
./scripts/dev-start.sh
# 또는
docker-compose --env-file .env.dev up -d
```

### 배포할 때  
```bash
./scripts/quick-deploy.sh
# 또는  
docker-compose --profile production up -d
```

### EC2에 배포할 때
```bash
curl -o ec2-install.sh https://raw.githubusercontent.com/djgnfj-svg/kkua/main/scripts/ec2-install.sh && chmod +x ec2-install.sh && ./ec2-install.sh
```

이 **단일 docker-compose.yml** 구조로 개발과 배포를 환경변수로 간단하게 전환할 수 있고, 설정 파일들을 체계적으로 관리할 수 있습니다.

## ✨ 통합 Docker Compose의 장점

1. **파일 개수 감소**: 3개 → 1개로 간소화
2. **일관된 설정**: 하나의 파일에서 모든 환경 관리  
3. **환경 전환 용이**: `.env.dev` ↔ `.env.prod` 전환으로 모드 변경
4. **유지보수 간편**: 설정 변경시 한 곳에서만 수정