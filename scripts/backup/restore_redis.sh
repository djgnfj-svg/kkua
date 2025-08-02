#!/bin/bash

# Redis 백업 복구 스크립트
# Redis 백업 파일에서 데이터를 복구합니다.

set -euo pipefail

# 설정 변수
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_ROOT}/backups/redis"
LOG_FILE="${PROJECT_ROOT}/logs/redis_restore.log"

# 환경변수 로드
if [ -f "${PROJECT_ROOT}/backend/.env" ]; then
    source "${PROJECT_ROOT}/backend/.env"
fi

# 기본값 설정
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"

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
    echo "복구 방법:"
    echo "  --rdb     RDB 파일로 복구 (기본값)"
    echo "  --aof     AOF 파일로 복구"
    echo "  --flush   복구 전 모든 데이터 삭제"
    echo ""
    echo "예시:"
    echo "  $0                                          # 최신 RDB 백업으로 복구"
    echo "  $0 redis_backup_20240115_143000.rdb.gz     # 특정 RDB 백업으로 복구"
    echo "  $0 --aof redis_backup_20240115_143000.aof.gz # AOF 백업으로 복구"
    echo "  $0 --flush redis_backup_20240115_143000.rdb.gz # 기존 데이터 삭제 후 복구"
    echo ""
    echo "사용 가능한 백업 파일:"
    if [ -d "$BACKUP_DIR" ]; then
        ls -lt "$BACKUP_DIR"/redis_backup_*.gz 2>/dev/null | head -5 || echo "  백업 파일이 없습니다."
    else
        echo "  백업 디렉토리가 없습니다: $BACKUP_DIR"
    fi
}

# 인수 파싱
parse_arguments() {
    RESTORE_TYPE="rdb"
    FLUSH_BEFORE_RESTORE=false
    BACKUP_FILE=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --rdb)
                RESTORE_TYPE="rdb"
                shift
                ;;
            --aof)
                RESTORE_TYPE="aof"
                shift
                ;;
            --flush)
                FLUSH_BEFORE_RESTORE=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                BACKUP_FILE="$1"
                shift
                ;;
        esac
    done
}

# 백업 파일 선택
select_backup_file() {
    if [ -z "$BACKUP_FILE" ]; then
        # 최신 백업 파일 자동 선택
        if [ "$RESTORE_TYPE" = "rdb" ]; then
            BACKUP_FILE=$(ls -t "$BACKUP_DIR"/redis_backup_*.rdb.gz 2>/dev/null | head -1)
        else
            BACKUP_FILE=$(ls -t "$BACKUP_DIR"/redis_backup_*.aof.gz 2>/dev/null | head -1)
        fi
        
        if [ -z "$BACKUP_FILE" ]; then
            error_exit "백업 파일을 찾을 수 없습니다 (타입: $RESTORE_TYPE)"
        fi
        log "최신 백업 파일 선택: $(basename "$BACKUP_FILE")"
    else
        # 사용자가 지정한 백업 파일
        if [[ "$BACKUP_FILE" == /* ]]; then
            # 절대 경로
            BACKUP_FILE="$BACKUP_FILE"
        else
            # 상대 경로 또는 파일명만
            BACKUP_FILE="${BACKUP_DIR}/$BACKUP_FILE"
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

# Redis 연결 테스트
test_redis_connection() {
    log "Redis 연결 테스트 중..."
    
    if command -v docker >/dev/null 2>&1; then
        if docker ps --format "table {{.Names}}" | grep -q "kkua-redis"; then
            docker exec kkua-redis-1 redis-cli ping > /dev/null 2>&1
        else
            error_exit "Redis Docker 컨테이너를 찾을 수 없습니다"
        fi
    else
        if [ -n "$REDIS_PASSWORD" ]; then
            redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" ping > /dev/null 2>&1
        else
            redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping > /dev/null 2>&1
        fi
    fi
    
    if [ $? -eq 0 ]; then
        log "Redis 연결 성공"
    else
        error_exit "Redis 연결 실패"
    fi
}

# 현재 Redis 데이터 백업 (복구 전 안전 백업)
backup_current_redis() {
    log "복구 전 현재 Redis 데이터 백업 중..."
    
    SAFETY_BACKUP_FILE="${BACKUP_DIR}/safety_backup_before_restore_$(date +%Y%m%d_%H%M%S).rdb.gz"
    
    if command -v docker >/dev/null 2>&1 && docker ps --format "table {{.Names}}" | grep -q "kkua-redis"; then
        # Docker 환경에서 안전 백업
        docker exec kkua-redis-1 redis-cli BGSAVE > /dev/null 2>&1
        
        # BGSAVE 완료 대기
        sleep 3
        
        # RDB 파일 복사 및 압축
        docker cp kkua-redis-1:/data/dump.rdb "/tmp/safety_backup.rdb" 2>/dev/null || true
        if [ -f "/tmp/safety_backup.rdb" ]; then
            gzip "/tmp/safety_backup.rdb"
            mv "/tmp/safety_backup.rdb.gz" "$SAFETY_BACKUP_FILE"
            log "안전 백업 완료: $(basename "$SAFETY_BACKUP_FILE")"
        else
            log "안전 백업 실패 - 계속 진행합니다"
        fi
    else
        log "로컬 Redis 환경에서는 안전 백업을 건너뜁니다"
    fi
}

# 사용자 확인
confirm_restore() {
    echo ""
    echo "⚠️  Redis 데이터 복구 확인 ⚠️"
    echo ""
    echo "Redis 서버: $REDIS_HOST:$REDIS_PORT"
    echo "백업 파일: $(basename "$BACKUP_FILE")"
    echo "복구 타입: $RESTORE_TYPE"
    echo "기존 데이터 삭제: $([ "$FLUSH_BEFORE_RESTORE" = "true" ] && echo "예" || echo "아니오")"
    echo "백업 생성 시간: $(stat -c %y "$BACKUP_FILE" 2>/dev/null || stat -f %Sm "$BACKUP_FILE" 2>/dev/null || echo "확인 불가")"
    echo ""
    
    if [ "$FLUSH_BEFORE_RESTORE" = "true" ]; then
        echo "⚠️  --flush 옵션으로 인해 현재 Redis의 모든 데이터가 삭제됩니다!"
        echo ""
    fi
    
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

# Redis 데이터 삭제 (선택적)
flush_redis_data() {
    if [ "$FLUSH_BEFORE_RESTORE" = "true" ]; then
        log "Redis 데이터 삭제 중..."
        
        if command -v docker >/dev/null 2>&1 && docker ps --format "table {{.Names}}" | grep -q "kkua-redis"; then
            docker exec kkua-redis-1 redis-cli FLUSHALL
        else
            if [ -n "$REDIS_PASSWORD" ]; then
                redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" FLUSHALL
            else
                redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" FLUSHALL
            fi
        fi
        
        log "Redis 데이터 삭제 완료"
    fi
}

# Redis 복구 실행 (RDB 방식)
perform_rdb_restore() {
    log "RDB 파일을 사용한 Redis 복구 시작..."
    
    # 임시 디렉토리에 백업 파일 압축 해제
    TEMP_DIR="/tmp/redis_restore_$$"
    mkdir -p "$TEMP_DIR"
    
    if [[ "$BACKUP_FILE" == *.gz ]]; then
        zcat "$BACKUP_FILE" > "$TEMP_DIR/dump.rdb"
    else
        cp "$BACKUP_FILE" "$TEMP_DIR/dump.rdb"
    fi
    
    if command -v docker >/dev/null 2>&1 && docker ps --format "table {{.Names}}" | grep -q "kkua-redis"; then
        # Docker 환경에서 복구
        log "Docker 환경에서 Redis 복구 실행"
        
        # Redis 서비스 중지
        docker exec kkua-redis-1 redis-cli SHUTDOWN NOSAVE 2>/dev/null || true
        sleep 2
        
        # RDB 파일 복사
        docker cp "$TEMP_DIR/dump.rdb" kkua-redis-1:/data/dump.rdb
        
        # Redis 재시작 (Docker Compose가 자동으로 재시작)
        docker-compose restart redis
        sleep 5
        
        # 연결 확인
        test_redis_connection
        
    else
        error_exit "로컬 Redis 환경에서의 RDB 복구는 수동으로 수행해야 합니다"
    fi
    
    # 임시 파일 정리
    rm -rf "$TEMP_DIR"
    
    log "RDB 복구 완료"
}

# Redis 복구 실행 (AOF 방식)
perform_aof_restore() {
    log "AOF 파일을 사용한 Redis 복구 시작..."
    
    if [[ "$BACKUP_FILE" != *".aof.gz" ]] && [[ "$BACKUP_FILE" != *".aof" ]]; then
        error_exit "AOF 복구를 위해서는 .aof 또는 .aof.gz 파일이 필요합니다"
    fi
    
    # 임시 디렉토리에 백업 파일 압축 해제
    TEMP_DIR="/tmp/redis_restore_$$"
    mkdir -p "$TEMP_DIR"
    
    if [[ "$BACKUP_FILE" == *.gz ]]; then
        zcat "$BACKUP_FILE" > "$TEMP_DIR/appendonly.aof"
    else
        cp "$BACKUP_FILE" "$TEMP_DIR/appendonly.aof"
    fi
    
    if command -v docker >/dev/null 2>&1 && docker ps --format "table {{.Names}}" | grep -q "kkua-redis"; then
        # Docker 환경에서 AOF 복구
        log "Docker 환경에서 AOF 복구 실행"
        
        # Redis 서비스 중지
        docker exec kkua-redis-1 redis-cli SHUTDOWN NOSAVE 2>/dev/null || true
        sleep 2
        
        # AOF 파일 복사
        docker cp "$TEMP_DIR/appendonly.aof" kkua-redis-1:/data/appendonly.aof
        
        # AOF 활성화 및 Redis 재시작
        # Redis 설정에서 AOF를 활성화해야 함
        docker-compose restart redis
        sleep 5
        
        # 연결 확인
        test_redis_connection
        
    else
        error_exit "로컬 Redis 환경에서의 AOF 복구는 수동으로 수행해야 합니다"
    fi
    
    # 임시 파일 정리
    rm -rf "$TEMP_DIR"
    
    log "AOF 복구 완료"
}

# 복구 검증
verify_restore() {
    log "복구 검증 중..."
    
    # 기본 키 개수 확인
    if command -v docker >/dev/null 2>&1 && docker ps --format "table {{.Names}}" | grep -q "kkua-redis"; then
        KEY_COUNT=$(docker exec kkua-redis-1 redis-cli DBSIZE 2>/dev/null || echo "0")
        MEMORY_USAGE=$(docker exec kkua-redis-1 redis-cli INFO memory | grep "used_memory_human:" | cut -d: -f2 | tr -d '\r' || echo "N/A")
    else
        if [ -n "$REDIS_PASSWORD" ]; then
            KEY_COUNT=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" DBSIZE 2>/dev/null || echo "0")
            MEMORY_USAGE=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" INFO memory | grep "used_memory_human:" | cut -d: -f2 || echo "N/A")
        else
            KEY_COUNT=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" DBSIZE 2>/dev/null || echo "0")
            MEMORY_USAGE=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" INFO memory | grep "used_memory_human:" | cut -d: -f2 || echo "N/A")
        fi
    fi
    
    log "복구 검증 완료:"
    log "  - 복구된 키 개수: $KEY_COUNT"
    log "  - 메모리 사용량: $MEMORY_USAGE"
}

# 복구 리포트 생성
generate_report() {
    log "복구 리포트 생성 중..."
    
    log "========== Redis 복구 완료 리포트 =========="
    log "Redis 서버: $REDIS_HOST:$REDIS_PORT"
    log "사용된 백업 파일: $(basename "$BACKUP_FILE")"
    log "복구 타입: $RESTORE_TYPE"
    log "복구 완료 시간: $(date)"
    log "로그 파일: $LOG_FILE"
    log "========================================"
}

# 메인 실행 함수
main() {
    # 로그 디렉토리 생성
    if [ ! -d "$(dirname "$LOG_FILE")" ]; then
        mkdir -p "$(dirname "$LOG_FILE")"
    fi
    
    log "Redis 복구 스크립트 시작"
    
    parse_arguments "$@"
    select_backup_file
    verify_backup_file
    test_redis_connection
    backup_current_redis
    confirm_restore
    flush_redis_data
    
    if [ "$RESTORE_TYPE" = "rdb" ]; then
        perform_rdb_restore
    else
        perform_aof_restore
    fi
    
    verify_restore
    generate_report
    
    log "Redis 복구 프로세스 완료"
}

# 스크립트 실행
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi