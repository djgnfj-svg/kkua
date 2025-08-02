# 끄아(KKUA) 관리 스크립트

이 폴더에는 끄아 게임 서비스 관리를 위한 간단한 스크립트들이 있습니다.

## 📁 폴더 구조

```
scripts/
├── logs.sh          # 로그 확인
├── status.sh        # 서비스 상태 확인  
├── backup/          # 백업 관련 스크립트들 (나중에 설정)
│   ├── backup_postgres.sh
│   ├── backup_redis.sh
│   ├── restore_postgres.sh
│   ├── restore_redis.sh
│   ├── setup_backup_cron.sh
│   └── systemd/     # systemd 백업 서비스들
└── README.md        # 이 파일
```

## 🚀 기본 사용법

### 서비스 상태 확인
```bash
# 개발환경 상태 확인
./scripts/status.sh

# 운영환경 상태 확인  
./scripts/status.sh production
```

### 로그 확인
```bash
# 사용 가능한 서비스 목록 보기
./scripts/logs.sh

# 백엔드 로그 확인
./scripts/logs.sh development backend

# 운영환경 백엔드 로그 확인
./scripts/logs.sh production backend
```

## 📋 주요 스크립트 (루트 폴더)

루트 폴더의 주요 관리 스크립트들:

```bash
# 서비스 배포/시작
./deploy.sh              # 개발환경 배포
./deploy.sh production   # 운영환경 배포

# 서비스 중지
./stop.sh               # 개발환경 중지
./stop.sh production    # 운영환경 중지
./stop.sh development --with-data  # 데이터까지 삭제하고 중지
```

## 🔧 나중에 설정할 것들

`backup/` 폴더에는 추후 설정할 백업 관련 스크립트들이 들어있습니다:

- **데이터베이스 백업**: PostgreSQL 자동 백업
- **Redis 백업**: Redis 데이터 백업
- **Cron 설정**: 자동 백업 스케줄링
- **Systemd 서비스**: 백업 서비스 등록

필요할 때 해당 스크립트들을 설정하여 사용하면 됩니다.