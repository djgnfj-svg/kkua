# 프로젝트 구조

## 📁 간단한 구조

```
kkua/
├── 🏗️  backend/                  # Python FastAPI 백엔드
├── 🎨 frontend/                  # React + TypeScript 프론트엔드
├── 🗄️  database/                # 한국어 단어 데이터 (35만+ 단어)
├── 📋 docs/                     # 프로젝트 문서들
│
├── docker-compose.yml          # 통합 Docker 설정
├── nginx.conf                  # Nginx 설정
├── .env.dev                   # 개발환경 변수
├── .env.prod                  # 프로덕션환경 변수
│
├── dev.sh                     # 개발 시작
└── deploy.sh                  # 프로덕션 배포
```

## 🚀 사용법

**개발할 때**
```bash
./dev.sh
```

**배포할 때**
```bash
./deploy.sh
```

**그게 다입니다!** ✨

## 🎯 특징

- **단일 docker-compose.yml**: 환경변수로 개발/프로덕션 모드 전환
- **간단한 스크립트**: 2개의 스크립트로 모든 것 해결
- **최소한의 설정**: 복잡한 설정 파일 없음
- **즉시 실행**: 클론 후 바로 `./dev.sh` 실행 가능