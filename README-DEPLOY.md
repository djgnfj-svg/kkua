# 끄아(KKUA) 간편 배포 가이드

Docker를 사용한 간단한 배포 방법입니다.

## 🚀 빠른 시작

### 1. 개발환경 배포
```bash
# 저장소 클론
git clone <repository-url>
cd kkua

# 개발환경 배포 (자동으로 .env 파일 생성됨)
./deploy.sh
```

### 2. 운영환경 배포
```bash
# 운영 환경 설정 파일 생성
cp backend/.env.production.example backend/.env.production

# 운영 환경 설정 편집 (중요!)
nano backend/.env.production

# 운영환경 배포
./deploy.sh production
```

## 📋 기본 명령어

```bash
# 서비스 시작/배포
./deploy.sh              # 개발환경
./deploy.sh production   # 운영환경

# 서비스 중지  
./stop.sh               # 개발환경
./stop.sh production    # 운영환경

# 서비스 상태 확인
./scripts/status.sh     # 개발환경
./scripts/status.sh production  # 운영환경

# 로그 확인
./scripts/logs.sh development backend    # 백엔드 로그
./scripts/logs.sh production backend     # 운영환경 백엔드 로그
```

## 🔧 접속 정보

### 개발환경
- **프론트엔드**: http://localhost:3000
- **백엔드**: http://localhost:8000  
- **API 문서**: http://localhost:8000/docs

### 운영환경
- **백엔드**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **프론트엔드**: 별도 웹서버에서 빌드된 정적 파일 서빙

## ⚠️ 운영환경 주의사항

운영 배포 전에 반드시 다음을 확인하세요:

1. **보안 설정**: `backend/.env.production`에서 SECRET_KEY 변경
2. **데이터베이스**: 운영용 PostgreSQL 연결 정보 설정
3. **도메인 설정**: CORS_ORIGINS에 실제 도메인 추가
4. **HTTPS**: SESSION_SECURE=true, 보안 헤더 활성화

## 🛠️ 문제 해결

### 서비스가 시작되지 않을 때
```bash
# 상태 확인
./scripts/status.sh

# 로그 확인
./scripts/logs.sh development backend
./scripts/logs.sh development frontend

# 완전 재시작
./stop.sh
./deploy.sh
```

### 데이터베이스 문제
```bash
# 데이터베이스 로그 확인
./scripts/logs.sh development db

# 데이터 초기화가 필요한 경우 (주의: 모든 데이터 삭제!)
./stop.sh development --with-data
./deploy.sh
```

## 📁 추가 기능 (나중에 설정)

- **백업 설정**: `scripts/backup/` 폴더의 백업 스크립트들
- **모니터링**: Sentry, 로그 수집 설정
- **SSL/HTTPS**: 인증서 설정 및 리버스 프록시
- **자동 배포**: CI/CD 파이프라인 구성

필요할 때 추가 설정하면 됩니다!