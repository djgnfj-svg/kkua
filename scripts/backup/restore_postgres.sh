#!/bin/bash

# PostgreSQL 백업 복구 스크립트
# 백업 파일에서 데이터베이스를 복구합니다.

set -euo pipefail

# 설정 변수
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_ROOT}/backups/postgres"
LOG_FILE="${PROJECT_ROOT}/logs/restore.log"

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

# 로깅 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 에러 처리 함수
error_exit() {
    log "ERROR: $1"
    exit 1
}

# 사용법 표시
show_usage() {
    echo "사용법: $0 [백업파일명]"
    echo ""
    echo "예시:"
    echo "  $0                                    # 최신 백업으로 복구"
    echo "  $0 kkua_backup_20240115_143000.sql.gz # 특정 백업으로 복구"
    echo ""
    echo "사용 가능한 백업 파일:"
    if [ -d "$BACKUP_DIR" ]; then
        ls -lt "$BACKUP_DIR"/kkua_backup_*.sql.gz 2>/dev/null | head -5 || echo "  백업 파일이 없습니다."
    else
        echo "  백업 디렉토리가 없습니다: $BACKUP_DIR"
    fi
}

# 백업 파일 선택
select_backup_file() {
    if [ $# -eq 0 ]; then
        # 최신 백업 파일 자동 선택
        BACKUP_FILE=$(ls -t "$BACKUP_DIR"/kkua_backup_*.sql.gz 2>/dev/null | head -1)
        if [ -z "$BACKUP_FILE" ]; then
            error_exit "백업 파일을 찾을 수 없습니다"
        fi
        log "최신 백업 파일 선택: $(basename "$BACKUP_FILE")"
    else
        # 사용자가 지정한 백업 파일
        if [[ "$1" == /* ]]; then
            BACKUP_FILE="$1"
        else
            BACKUP_FILE="${BACKUP_DIR}/$1"
        fi
        
        if [ ! -f "$BACKUP_FILE" ]; then
            error_exit "백업 파일을 찾을 수 없습니다: $BACKUP_FILE"
        fi
    fi
}

# 백업 파일 검증
verify_backup_file() {
    log "백업 파일 검증 중: $(basename "$BACKUP_FILE")"
    
    # 파일 존재 및 읽기 권한 확인
    if [ ! -r "$BACKUP_FILE" ]; then
        error_exit "백업 파일을 읽을 수 없습니다: $BACKUP_FILE"
    fi
    
    # 압축 파일 무결성 확인
    if [[ "$BACKUP_FILE" == *.gz ]]; then
        gzip -t "$BACKUP_FILE"
        if [ $? -ne 0 ]; then
            error_exit "백업 파일이 손상되었습니다: $BACKUP_FILE"
        fi
    fi
    
    log "백업 파일 검증 완료"
}

# 데이터베이스 연결 테스트
test_connection() {
    log "데이터베이스 연결 테스트 중..."
    
    if command -v docker >/dev/null 2>&1; then
        if docker ps --format "table {{.Names}}" | grep -q "kkua-db"; then
            docker exec kkua-db-1 pg_isready -h localhost -p 5432 -U "$DB_USER" > /dev/null 2>&1
        else
            error_exit "PostgreSQL Docker 컨테이너를 찾을 수 없습니다"
        fi
    else
        PGPASSWORD="$DB_PASSWORD" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1
    fi
    
    if [ $? -eq 0 ]; then
        log "데이터베이스 연결 성공"
    else
        error_exit "데이터베이스 연결 실패"
    fi
}

# 현재 데이터베이스 백업 (복구 전 안전 백업)
backup_current_db() {
    log "복구 전 현재 데이터베이스 백업 중..."
    
    SAFETY_BACKUP_FILE="${BACKUP_DIR}/safety_backup_before_restore_$(date +%Y%m%d_%H%M%S).sql.gz"
    
    if command -v docker >/dev/null 2>&1 && docker ps --format "table {{.Names}}" | grep -q "kkua-db"; then
        docker exec kkua-db-1 pg_dump -h localhost -U "$DB_USER" -d "$DB_NAME" --verbose --clean --no-owner --no-privileges | gzip > "$SAFETY_BACKUP_FILE" 2>> "$LOG_FILE"
    else
        PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --verbose --clean --no-owner --no-privileges | gzip > "$SAFETY_BACKUP_FILE" 2>> "$LOG_FILE"
    fi
    
    if [ $? -eq 0 ]; then
        log "안전 백업 완료: $(basename "$SAFETY_BACKUP_FILE")"
    else
        error_exit "안전 백업 실패"
    fi
}

# 사용자 확인
confirm_restore() {
    echo ""
    echo "⚠️  데이터베이스 복구 확인 ⚠️"
    echo ""
    echo "데이터베이스: $DB_NAME"
    echo "백업 파일: $(basename "$BACKUP_FILE")"
    echo "백업 생성 시간: $(stat -c %y "$BACKUP_FILE" 2>/dev/null || stat -f %Sm "$BACKUP_FILE" 2>/dev/null || echo "확인 불가")"
    echo ""
    echo "현재 데이터베이스의 모든 데이터가 백업 파일의 데이터로 교체됩니다!"
    echo ""
    
    if [ "${FORCE_RESTORE:-false}" != "true" ]; then
        read -p "계속하시겠습니까? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            log "복구 작업이 취소되었습니다"
            exit 0
        fi
    else
        log "FORCE_RESTORE=true로 인해 확인 없이 진행합니다"
    fi
}

# 데이터베이스 복구 실행
perform_restore() {
    log "데이터베이스 복구 시작..."
    
    if command -v docker >/dev/null 2>&1 && docker ps --format "table {{.Names}}" | grep -q "kkua-db"; then
        # Docker 환경에서 복구
        log "Docker 환경에서 복구 실행"
        if [[ "$BACKUP_FILE" == *.gz ]]; then
            zcat "$BACKUP_FILE" | docker exec -i kkua-db-1 psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 >> "$LOG_FILE" 2>&1
        else
            cat "$BACKUP_FILE" | docker exec -i kkua-db-1 psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 >> "$LOG_FILE" 2>&1
        fi
    else
        # 로컬 PostgreSQL에서 복구
        log "로컬 PostgreSQL에서 복구 실행"
        if [[ "$BACKUP_FILE" == *.gz ]]; then
            zcat "$BACKUP_FILE" | PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 >> "$LOG_FILE" 2>&1
        else
            PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -f "$BACKUP_FILE" >> "$LOG_FILE" 2>&1
        fi
    fi
    
    if [ $? -eq 0 ]; then
        log "데이터베이스 복구 완료"
    else
        error_exit "데이터베이스 복구 실패"
    fi
}

# 복구 검증
verify_restore() {
    log "복구 검증 중..."
    
    # 기본 테이블 존재 확인
    if command -v docker >/dev/null 2>&1 && docker ps --format "table {{.Names}}" | grep -q "kkua-db"; then
        TABLE_COUNT=$(docker exec kkua-db-1 psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ')
    else
        TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ')
    fi
    
    if [ -n "$TABLE_COUNT" ] && [ "$TABLE_COUNT" -gt 0 ]; then
        log "복구 검증 완료: $TABLE_COUNT 개의 테이블이 확인되었습니다"
    else
        log "경고: 테이블 수를 확인할 수 없습니다"
    fi
}

# 복구 리포트 생성
generate_report() {
    log "복구 리포트 생성 중..."
    
    log "========== 복구 완료 리포트 =========="
    log "복구된 데이터베이스: $DB_NAME"
    log "사용된 백업 파일: $(basename "$BACKUP_FILE")"
    log "복구 완료 시간: $(date)"
    log "로그 파일: $LOG_FILE"
    log "=================================="
}

# 메인 실행 함수
main() {
    # 도움말 표시
    if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
        show_usage
        exit 0
    fi
    
    log "PostgreSQL 복구 스크립트 시작"
    
    # 로그 디렉토리 생성
    if [ ! -d "$(dirname "$LOG_FILE")" ]; then
        mkdir -p "$(dirname "$LOG_FILE")"
    fi
    
    select_backup_file "$@"
    verify_backup_file
    test_connection
    backup_current_db
    confirm_restore
    perform_restore
    verify_restore
    generate_report
    
    log "복구 프로세스 완료"
}

# 스크립트 실행
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi