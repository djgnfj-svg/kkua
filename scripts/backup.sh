#!/bin/bash

# 데이터베이스 백업 스크립트
set -euo pipefail

BACKUP_DIR="/opt/kkua/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_CONTAINER="kkua-db"

# 색상 설정
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR"

log_info "데이터베이스 백업을 시작합니다..."

# PostgreSQL 백업
if docker ps | grep -q "$DB_CONTAINER"; then
    BACKUP_FILE="$BACKUP_DIR/kkua_db_backup_${DATE}.sql"
    
    docker exec "$DB_CONTAINER" pg_dump -U postgres kkua_db > "$BACKUP_FILE"
    
    # 압축
    gzip "$BACKUP_FILE"
    
    log_success "백업 완료: ${BACKUP_FILE}.gz"
    
    # 7일 이전 백업 파일 삭제
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
    
    log_info "7일 이전 백업 파일을 정리했습니다."
else
    log_error "데이터베이스 컨테이너가 실행 중이지 않습니다."
    exit 1
fi