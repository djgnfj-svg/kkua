# 🗄️ 백업 및 복구 가이드

## 개요

KKUA 프로젝트는 PostgreSQL과 Redis 데이터베이스를 사용하며, 각각에 대한 자동화된 백업 및 복구 시스템을 제공합니다.

## 📁 백업 파일 구조

```
backups/
├── postgres/                          # PostgreSQL 백업
│   ├── kkua_backup_20240115_020000.sql.gz
│   └── safety_backup_before_restore_*.sql.gz
└── redis/                             # Redis 백업
    ├── redis_backup_20240115_030000.rdb.gz      # RDB 파일
    ├── redis_backup_20240115_030000.aof.gz      # AOF 파일 (선택적)
    ├── redis_backup_20240115_030000_memory.json.gz  # 메모리 상태
    └── redis_backup_20240115_030000_config.conf.gz  # Redis 설정
```

## 🔄 PostgreSQL 백업 및 복구

### 자동 백업 설정

#### 1. Cron 작업으로 설정 (권장)
```bash
# 크론 작업 설치
./scripts/setup_backup_cron.sh --install

# 상태 확인
./scripts/setup_backup_cron.sh --status

# 제거
./scripts/setup_backup_cron.sh --uninstall
```

#### 2. systemd 타이머로 설정 (서버 환경)
```bash
# systemd 서비스 설치
sudo ./scripts/systemd/setup_systemd_backup.sh install

# 상태 확인
sudo ./scripts/systemd/setup_systemd_backup.sh status

# 수동 백업 실행
sudo ./scripts/systemd/setup_systemd_backup.sh run
```

### 수동 백업

```bash
# PostgreSQL 백업 실행
./scripts/backup_postgres.sh

# 환경변수 설정 후 백업
DATABASE_PASSWORD=your_password ./scripts/backup_postgres.sh

# 복구 테스트 포함 백업
TEST_RESTORE=true ./scripts/backup_postgres.sh
```

### PostgreSQL 복구

```bash
# 최신 백업으로 복구
./scripts/restore_postgres.sh

# 특정 백업으로 복구
./scripts/restore_postgres.sh kkua_backup_20240115_020000.sql.gz

# 강제 복구 (확인 없이)
FORCE_RESTORE=true ./scripts/restore_postgres.sh backup_file.sql.gz
```

## 📊 Redis 백업 및 복구

### 자동 백업 설정

Redis 백업은 PostgreSQL과 동일한 방식으로 설정됩니다:

```bash
# Cron 또는 systemd로 자동 설정
./scripts/setup_backup_cron.sh --install
```

### 수동 백업

```bash
# Redis 백업 실행 (RDB + 메모리 상태 + 설정)
./scripts/backup_redis.sh

# AOF 백업 포함
BACKUP_AOF=true ./scripts/backup_redis.sh
```

### Redis 복구

```bash
# 최신 RDB 백업으로 복구
./scripts/restore_redis.sh

# 특정 RDB 백업으로 복구
./scripts/restore_redis.sh redis_backup_20240115_030000.rdb.gz

# AOF 백업으로 복구
./scripts/restore_redis.sh --aof redis_backup_20240115_030000.aof.gz

# 기존 데이터 삭제 후 복구
./scripts/restore_redis.sh --flush redis_backup_20240115_030000.rdb.gz
```

## 🐳 Docker 환경에서의 백업

### Docker Compose를 이용한 백업

**docker-compose.yml에 백업 서비스 추가:**
```yaml
services:
  # ... 기존 서비스들 ...
  
  backup:
    build: ./backend
    volumes:
      - ./backups:/app/backups
      - ./scripts:/app/scripts
      - ./logs:/app/logs
      - ./backend/.env:/app/.env
    environment:
      - DATABASE_HOST=db
      - REDIS_HOST=redis
    depends_on:
      - db
      - redis
    restart: "no"
    profiles: ["backup"]
```

### 백업 실행

```bash
# PostgreSQL 백업
docker-compose --profile backup run --rm backup /app/scripts/backup_postgres.sh

# Redis 백업
docker-compose --profile backup run --rm backup /app/scripts/backup_redis.sh

# 모든 백업 실행
docker-compose --profile backup run --rm backup sh -c "/app/scripts/backup_postgres.sh && /app/scripts/backup_redis.sh"
```

### 복구 실행

```bash
# PostgreSQL 복구
docker-compose --profile backup run --rm backup /app/scripts/restore_postgres.sh

# Redis 복구
docker-compose --profile backup run --rm backup /app/scripts/restore_redis.sh
```

## ⚙️ 백업 설정 및 옵션

### 환경변수 설정

**.env 파일에 추가할 백업 관련 설정:**
```bash
# 백업 보관 기간 (일)
BACKUP_RETENTION_DAYS=7

# Redis 백업 옵션
BACKUP_AOF=true              # AOF 백업 활성화
REDIS_PASSWORD=your_password # Redis 비밀번호 (있을 경우)

# 복구 옵션
FORCE_RESTORE=false          # 확인 없이 복구 (위험!)
TEST_RESTORE=false           # 백업 후 복구 테스트
```

### 크론 작업 스케줄

기본 백업 스케줄:
- **PostgreSQL**: 매일 새벽 2:00
- **Redis**: 매일 새벽 3:00  
- **정리 작업**: 매주 일요일 새벽 4:00 (30일 이상 된 백업 삭제)

## 🔍 백업 상태 모니터링

### 로그 파일 확인

```bash
# 백업 로그
tail -f logs/backup.log

# Redis 백업 로그
tail -f logs/redis_backup.log

# 복구 로그
tail -f logs/restore.log

# Cron 실행 로그
tail -f logs/cron.log
```

### 백업 상태 확인

```bash
# 백업 파일 목록
ls -la backups/postgres/
ls -la backups/redis/

# 백업 크기 확인
du -sh backups/

# systemd 서비스 상태 (systemd 사용 시)
sudo systemctl status kkua-postgres-backup.timer
sudo systemctl status kkua-redis-backup.timer
```

## 🚨 재해 복구 절차

### 1. 전체 데이터 손실 시

```bash
# 1. 서비스 중지
docker-compose down

# 2. 데이터 볼륨 확인
docker volume ls

# 3. 백업에서 복구
./scripts/restore_postgres.sh
./scripts/restore_redis.sh

# 4. 서비스 재시작
docker-compose up -d

# 5. 복구 확인
./scripts/setup_backup_cron.sh --test
```

### 2. 부분 데이터 손실 시

```bash
# 특정 시점 백업 선택
ls -la backups/postgres/ | head -10

# 해당 시점으로 복구
./scripts/restore_postgres.sh kkua_backup_YYYYMMDD_HHMMSS.sql.gz
```

### 3. 복구 검증

```bash
# 데이터베이스 연결 테스트
curl http://localhost:8000/health/detailed

# 애플리케이션 기능 테스트
curl http://localhost:8000/gamerooms

# 로그 확인
docker-compose logs backend | tail -20
```

## 🔒 보안 고려사항

### 백업 파일 보안

1. **백업 파일 암호화** (프로덕션 권장):
```bash
# GPG로 백업 암호화
gpg --symmetric --cipher-algo AES256 backup_file.sql.gz

# 복호화
gpg --decrypt backup_file.sql.gz.gpg > backup_file.sql.gz
```

2. **원격 저장소 동기화**:
```bash
# rsync로 원격 백업
rsync -avz --delete backups/ user@backup-server:/backup/kkua/

# AWS S3 동기화
aws s3 sync backups/ s3://your-backup-bucket/kkua/
```

### 권한 설정

```bash
# 백업 디렉토리 권한
chmod 750 backups/
chmod 640 backups/*/*.gz

# 스크립트 실행 권한
chmod 750 scripts/*.sh
```

## 📈 성능 최적화

### 백업 성능 개선

1. **압축 레벨 조정**: 기본 gzip 대신 pigz 사용
2. **병렬 백업**: PostgreSQL과 Redis 동시 백업
3. **증분 백업**: 대용량 데이터베이스용 증분 백업 구현

### 복구 성능 개선

1. **SSD 사용**: 백업 파일을 SSD에 저장
2. **메모리 증가**: 복구 시 PostgreSQL 메모리 설정 증가
3. **병렬 복구**: 여러 데이터베이스 동시 복구

## 🔧 트러블슈팅

### 일반적인 문제들

**1. 백업 파일 권한 오류**
```bash
# 해결: 권한 수정
sudo chown -R $USER:$USER backups/
chmod -R 755 backups/
```

**2. Docker 컨테이너 연결 실패**
```bash
# 해결: 컨테이너 상태 확인
docker-compose ps
docker-compose logs db redis
```

**3. 디스크 공간 부족**
```bash
# 해결: 오래된 백업 정리
find backups/ -name "*.gz" -mtime +30 -delete

# 또는 수동 정리
./scripts/setup_backup_cron.sh --status
```

**4. 복구 실패**
```bash
# 해결: 로그 확인 및 수동 복구
tail -50 logs/restore.log

# 데이터베이스 연결 확인
docker exec kkua-db-1 pg_isready -U postgres
```

### 백업 검증

```bash
# 백업 무결성 확인
gzip -t backups/postgres/*.gz
gzip -t backups/redis/*.gz

# 복구 테스트
TEST_RESTORE=true ./scripts/backup_postgres.sh
```

이 가이드를 통해 KKUA 프로젝트의 데이터를 안전하게 백업하고 필요시 신속하게 복구할 수 있습니다.