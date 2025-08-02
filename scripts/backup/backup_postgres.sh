#!/bin/bash

# PostgreSQL 자동 백업 스크립트
# 데이터베이스 백업을 생성하고 오래된 백업 파일을 정리합니다.

set -euo pipefail  # 엄격한 에러 처리

# 설정 변수
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_ROOT}/backups/postgres"
LOG_FILE="${PROJECT_ROOT}/logs/backup.log"

# 환경변수 로드
if [ -f "${PROJECT_ROOT}/backend/.env" ]; then
    source "${PROJECT_ROOT}/backend/.env"
fi

# 기본값 설정
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-mydb}"
DB_USER="${DATABASE_USER:-postgres}"
DB_PASSWORD="${DATABASE_PASSWORD:-mysecretpassword}"

# 백업 보관 기간 (일)
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

# 타임스탬프 생성
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILENAME="kkua_backup_${TIMESTAMP}.sql"
BACKUP_COMPRESSED="kkua_backup_${TIMESTAMP}.sql.gz"

# 로깅 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 에러 처리 함수
error_exit() {
    log "ERROR: $1"
    exit 1
}

# 백업 디렉토리 생성
setup_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        log "백업 디렉토리 생성: $BACKUP_DIR"
    fi
    
    if [ ! -d "$(dirname "$LOG_FILE")" ]; then
        mkdir -p "$(dirname "$LOG_FILE")"
        log "로그 디렉토리 생성: $(dirname "$LOG_FILE")"
    fi
}

# 데이터베이스 연결 테스트
test_connection() {
    log "데이터베이스 연결 테스트 중..."
    
    if command -v docker >/dev/null 2>&1; then
        # Docker 환경에서 실행
        if docker ps --format "table {{.Names}}" | grep -q "kkua-db"; then
            docker exec kkua-db-1 pg_isready -h localhost -p 5432 -U "$DB_USER" > /dev/null 2>&1
        else
            error_exit "PostgreSQL Docker 컨테이너를 찾을 수 없습니다."
        fi
    else
        # 로컬 PostgreSQL 연결 테스트
        PGPASSWORD="$DB_PASSWORD" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1
    fi
    
    if [ $? -eq 0 ]; then
        log "데이터베이스 연결 성공"
    else
        error_exit "데이터베이스 연결 실패"
    fi
}

# 백업 실행
perform_backup() {
    log "백업 시작: $DB_NAME"
    
    if command -v docker >/dev/null 2>&1 && docker ps --format "table {{.Names}}" | grep -q "kkua-db"; then
        # Docker 환경에서 백업
        log "Docker 환경에서 백업 실행"
        docker exec kkua-db-1 pg_dump -h localhost -U "$DB_USER" -d "$DB_NAME" --verbose --clean --no-owner --no-privileges > "${BACKUP_DIR}/${BACKUP_FILENAME}" 2>> "$LOG_FILE"
    else
        # 로컬 PostgreSQL에서 백업
        log "로컬 PostgreSQL에서 백업 실행"
        PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --verbose --clean --no-owner --no-privileges > "${BACKUP_DIR}/${BACKUP_FILENAME}" 2>> "$LOG_FILE"
    fi
    
    if [ $? -eq 0 ]; then
        log "백업 완료: ${BACKUP_FILENAME}"
    else
        error_exit "백업 실패"
    fi
}

# 백업 압축
compress_backup() {
    log "백업 파일 압축 중..."
    
    gzip "${BACKUP_DIR}/${BACKUP_FILENAME}"
    
    if [ $? -eq 0 ]; then
        log "압축 완료: ${BACKUP_COMPRESSED}"
        
        # 압축된 파일 크기 확인
        BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_COMPRESSED}" | cut -f1)
        log "백업 파일 크기: $BACKUP_SIZE"
    else
        error_exit "백업 압축 실패"
    fi
}

# 백업 무결성 검증
verify_backup() {
    log "백업 무결성 검증 중..."
    
    # 압축 파일 무결성 확인
    gzip -t "${BACKUP_DIR}/${BACKUP_COMPRESSED}"
    
    if [ $? -eq 0 ]; then
        log "백업 무결성 검증 완료"
    else
        error_exit "백업 파일이 손상되었습니다"
    fi
}

# 오래된 백업 파일 정리
cleanup_old_backups() {
    log "오래된 백업 파일 정리 중 (${RETENTION_DAYS}일 이상 된 파일)..."
    
    # 7일 이상 된 백업 파일 찾기 및 삭제
    OLD_BACKUPS=$(find "$BACKUP_DIR" -name "kkua_backup_*.sql.gz" -mtime +$RETENTION_DAYS 2>/dev/null || true)
    
    if [ -n "$OLD_BACKUPS" ]; then
        echo "$OLD_BACKUPS" | while read -r old_backup; do
            if [ -f "$old_backup" ]; then
                rm "$old_backup"
                log "삭제된 오래된 백업: $(basename "$old_backup")"
            fi
        done
    else
        log "정리할 오래된 백업 파일이 없습니다"
    fi
}

# 백업 상태 리포트 생성
generate_report() {
    log "백업 상태 리포트 생성 중..."
    
    BACKUP_COUNT=$(find "$BACKUP_DIR" -name "kkua_backup_*.sql.gz" | wc -l)
    TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "N/A")
    
    log "========== 백업 상태 리포트 =========="
    log "백업 디렉토리: $BACKUP_DIR"
    log "백업 파일 수: $BACKUP_COUNT"
    log "총 백업 크기: $TOTAL_SIZE"
    log "보관 기간: ${RETENTION_DAYS}일"
    log "최신 백업: ${BACKUP_COMPRESSED}"
    log "===================================="
}

# 백업 복구 테스트 (선택적)
test_restore() {
    if [ "${TEST_RESTORE:-false}" = "true" ]; then
        log "백업 복구 테스트 시작..."
        
        # 테스트용 임시 데이터베이스 이름
        TEST_DB="kkua_test_restore_$(date +%s)"
        
        if command -v docker >/dev/null 2>&1 && docker ps --format "table {{.Names}}" | grep -q "kkua-db"; then
            # Docker 환경에서 복구 테스트
            docker exec kkua-db-1 createdb -U "$DB_USER" "$TEST_DB" 2>/dev/null || true
            zcat "${BACKUP_DIR}/${BACKUP_COMPRESSED}" | docker exec -i kkua-db-1 psql -U "$DB_USER" -d "$TEST_DB" > /dev/null 2>&1
            
            if [ $? -eq 0 ]; then
                log "백업 복구 테스트 성공"
                # 테스트 데이터베이스 삭제
                docker exec kkua-db-1 dropdb -U "$DB_USER" "$TEST_DB" 2>/dev/null || true
            else
                log "백업 복구 테스트 실패"
            fi
        else
            log "Docker 환경이 아니므로 복구 테스트를 건너뜁니다"
        fi
    fi
}

# 메인 실행 함수
main() {
    log "PostgreSQL 백업 스크립트 시작"
    
    setup_backup_dir
    test_connection
    perform_backup
    compress_backup
    verify_backup
    cleanup_old_backups
    test_restore
    generate_report
    
    log "백업 프로세스 완료"
}

# 스크립트 실행
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi