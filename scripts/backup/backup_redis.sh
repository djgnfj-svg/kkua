#!/bin/bash

# Redis 자동 백업 스크립트
# Redis 데이터를 백업하고 오래된 백업 파일을 정리합니다.

set -euo pipefail

# 설정 변수
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_ROOT}/backups/redis"
LOG_FILE="${PROJECT_ROOT}/logs/redis_backup.log"

# 환경변수 로드
if [ -f "${PROJECT_ROOT}/backend/.env" ]; then
    source "${PROJECT_ROOT}/backend/.env"
fi

# 기본값 설정
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"
REDIS_URL="${REDIS_URL:-redis://redis:6379/0}"

# 백업 보관 기간 (일)
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

# 타임스탬프 생성
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILENAME="redis_backup_${TIMESTAMP}"

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

# Redis 연결 테스트
test_redis_connection() {
    log "Redis 연결 테스트 중..."
    
    if command -v docker >/dev/null 2>&1; then
        # Docker 환경에서 실행
        if docker ps --format "table {{.Names}}" | grep -q "kkua-redis"; then
            docker exec kkua-redis-1 redis-cli ping > /dev/null 2>&1
        else
            error_exit "Redis Docker 컨테이너를 찾을 수 없습니다."
        fi
    else
        # 로컬 Redis 연결 테스트
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

# Redis 백업 실행 (RDB 방식)
perform_rdb_backup() {
    log "Redis RDB 백업 시작..."
    
    if command -v docker >/dev/null 2>&1 && docker ps --format "table {{.Names}}" | grep -q "kkua-redis"; then
        # Docker 환경에서 RDB 백업
        log "Docker 환경에서 RDB 백업 실행"
        
        # BGSAVE 명령으로 백그라운드에서 RDB 생성
        docker exec kkua-redis-1 redis-cli BGSAVE > /dev/null 2>&1
        
        # BGSAVE 완료 대기
        log "RDB 생성 대기 중..."
        while true; do
            LAST_SAVE=$(docker exec kkua-redis-1 redis-cli LASTSAVE 2>/dev/null || echo "0")
            sleep 2
            CURRENT_SAVE=$(docker exec kkua-redis-1 redis-cli LASTSAVE 2>/dev/null || echo "0")
            if [ "$CURRENT_SAVE" -gt "$LAST_SAVE" ]; then
                break
            fi
            log "RDB 생성 중..."
        done
        
        # RDB 파일 복사
        docker cp kkua-redis-1:/data/dump.rdb "${BACKUP_DIR}/${BACKUP_FILENAME}.rdb"
        
    else
        # 로컬 Redis에서 백업
        log "로컬 Redis에서 RDB 백업 실행"
        
        if [ -n "$REDIS_PASSWORD" ]; then
            redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" BGSAVE
        else
            redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" BGSAVE
        fi
        
        # RDB 파일 위치는 Redis 설정에 따라 다름
        # 일반적으로 /var/lib/redis/dump.rdb
        if [ -f "/var/lib/redis/dump.rdb" ]; then
            cp /var/lib/redis/dump.rdb "${BACKUP_DIR}/${BACKUP_FILENAME}.rdb"
        else
            error_exit "RDB 파일을 찾을 수 없습니다"
        fi
    fi
    
    if [ -f "${BACKUP_DIR}/${BACKUP_FILENAME}.rdb" ]; then
        log "RDB 백업 완료: ${BACKUP_FILENAME}.rdb"
    else
        error_exit "RDB 백업 실패"
    fi
}

# Redis 백업 실행 (AOF 방식, 선택적)
perform_aof_backup() {
    if [ "${BACKUP_AOF:-false}" = "true" ]; then
        log "Redis AOF 백업 시작..."
        
        if command -v docker >/dev/null 2>&1 && docker ps --format "table {{.Names}}" | grep -q "kkua-redis"; then
            # AOF 파일 확인 및 복사
            if docker exec kkua-redis-1 test -f /data/appendonly.aof; then
                docker cp kkua-redis-1:/data/appendonly.aof "${BACKUP_DIR}/${BACKUP_FILENAME}.aof"
                log "AOF 백업 완료: ${BACKUP_FILENAME}.aof"
            else
                log "AOF 파일이 존재하지 않습니다 (AOF가 비활성화되어 있을 수 있음)"
            fi
        else
            # 로컬 Redis AOF 백업
            if [ -f "/var/lib/redis/appendonly.aof" ]; then
                cp /var/lib/redis/appendonly.aof "${BACKUP_DIR}/${BACKUP_FILENAME}.aof"
                log "AOF 백업 완료: ${BACKUP_FILENAME}.aof"
            else
                log "AOF 파일이 존재하지 않습니다"
            fi
        fi
    fi
}

# 메모리 상태 백업 (JSON 방식)
perform_memory_backup() {
    log "Redis 메모리 상태 백업 시작..."
    
    MEMORY_BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILENAME}_memory.json"
    
    if command -v docker >/dev/null 2>&1 && docker ps --format "table {{.Names}}" | grep -q "kkua-redis"; then
        # Docker 환경에서 메모리 백업
        {
            echo "{"
            echo "  \"timestamp\": \"$(date -Iseconds)\","
            echo "  \"redis_info\": {"
            
            # Redis 정보 수집
            docker exec kkua-redis-1 redis-cli INFO server | sed 's/^/    "/' | sed 's/:/": "/' | sed 's/$/",/' | head -20
            
            echo "  },"
            echo "  \"databases\": {"
            
            # 각 데이터베이스의 키 정보
            for db in 0 1 2; do
                echo "    \"db${db}\": {"
                KEY_COUNT=$(docker exec kkua-redis-1 redis-cli -n $db DBSIZE 2>/dev/null || echo "0")
                echo "      \"key_count\": $KEY_COUNT,"
                
                # 게임 관련 키 샘플 (처음 10개)
                echo "      \"sample_keys\": ["
                docker exec kkua-redis-1 redis-cli -n $db KEYS "*" | head -10 | sed 's/^/        "/' | sed 's/$/",/' | sed '$ s/,$//'
                echo "      ]"
                echo "    }$([ $db -lt 2 ] && echo ",")"
            done
            
            echo "  }"
            echo "}"
        } > "$MEMORY_BACKUP_FILE" 2>/dev/null
        
    else
        # 로컬 Redis에서 메모리 백업
        {
            echo "{"
            echo "  \"timestamp\": \"$(date -Iseconds)\","
            echo "  \"redis_info\": {"
            
            if [ -n "$REDIS_PASSWORD" ]; then
                redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" INFO server | sed 's/^/    "/' | sed 's/:/": "/' | sed 's/$/",/' | head -20
            else
                redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" INFO server | sed 's/^/    "/' | sed 's/:/": "/' | sed 's/$/",/' | head -20
            fi
            
            echo "  }"
            echo "}"
        } > "$MEMORY_BACKUP_FILE" 2>/dev/null
    fi
    
    if [ -f "$MEMORY_BACKUP_FILE" ]; then
        log "메모리 상태 백업 완료: ${BACKUP_FILENAME}_memory.json"
    else
        log "메모리 상태 백업 실패"
    fi
}

# 백업 압축
compress_backups() {
    log "백업 파일 압축 중..."
    
    # RDB 파일 압축
    if [ -f "${BACKUP_DIR}/${BACKUP_FILENAME}.rdb" ]; then
        gzip "${BACKUP_DIR}/${BACKUP_FILENAME}.rdb"
        log "RDB 파일 압축 완료: ${BACKUP_FILENAME}.rdb.gz"
    fi
    
    # AOF 파일 압축 (있을 경우)
    if [ -f "${BACKUP_DIR}/${BACKUP_FILENAME}.aof" ]; then
        gzip "${BACKUP_DIR}/${BACKUP_FILENAME}.aof"
        log "AOF 파일 압축 완료: ${BACKUP_FILENAME}.aof.gz"
    fi
    
    # 메모리 상태 파일 압축
    if [ -f "${BACKUP_DIR}/${BACKUP_FILENAME}_memory.json" ]; then
        gzip "${BACKUP_DIR}/${BACKUP_FILENAME}_memory.json"
        log "메모리 상태 파일 압축 완료: ${BACKUP_FILENAME}_memory.json.gz"
    fi
}

# 백업 무결성 검증
verify_backups() {
    log "백업 무결성 검증 중..."
    
    # 압축 파일들 검증
    for backup_file in "${BACKUP_DIR}/${BACKUP_FILENAME}."*.gz; do
        if [ -f "$backup_file" ]; then
            if gzip -t "$backup_file"; then
                log "검증 성공: $(basename "$backup_file")"
            else
                error_exit "백업 파일이 손상되었습니다: $(basename "$backup_file")"
            fi
        fi
    done
}

# 오래된 백업 파일 정리
cleanup_old_backups() {
    log "오래된 Redis 백업 파일 정리 중 (${RETENTION_DAYS}일 이상 된 파일)..."
    
    # 백업 파일 패턴으로 찾기 및 삭제
    OLD_BACKUPS=$(find "$BACKUP_DIR" -name "redis_backup_*.gz" -mtime +$RETENTION_DAYS 2>/dev/null || true)
    
    if [ -n "$OLD_BACKUPS" ]; then
        echo "$OLD_BACKUPS" | while read -r old_backup; do
            if [ -f "$old_backup" ]; then
                rm "$old_backup"
                log "삭제된 오래된 백업: $(basename "$old_backup")"
            fi
        done
    else
        log "정리할 오래된 Redis 백업 파일이 없습니다"
    fi
}

# Redis 설정 백업
backup_redis_config() {
    log "Redis 설정 백업 중..."
    
    CONFIG_BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILENAME}_config.conf"
    
    if command -v docker >/dev/null 2>&1 && docker ps --format "table {{.Names}}" | grep -q "kkua-redis"; then
        # Docker 환경에서 설정 백업
        docker exec kkua-redis-1 redis-cli CONFIG GET "*" > "$CONFIG_BACKUP_FILE" 2>/dev/null || true
    else
        # 로컬 Redis 설정 백업
        if [ -n "$REDIS_PASSWORD" ]; then
            redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" CONFIG GET "*" > "$CONFIG_BACKUP_FILE" 2>/dev/null || true
        else
            redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" CONFIG GET "*" > "$CONFIG_BACKUP_FILE" 2>/dev/null || true
        fi
    fi
    
    if [ -f "$CONFIG_BACKUP_FILE" ] && [ -s "$CONFIG_BACKUP_FILE" ]; then
        gzip "$CONFIG_BACKUP_FILE"
        log "Redis 설정 백업 완료: ${BACKUP_FILENAME}_config.conf.gz"
    else
        log "Redis 설정 백업 실패 또는 빈 파일"
        rm -f "$CONFIG_BACKUP_FILE"
    fi
}

# 백업 상태 리포트 생성
generate_report() {
    log "Redis 백업 상태 리포트 생성 중..."
    
    BACKUP_COUNT=$(find "$BACKUP_DIR" -name "redis_backup_*.gz" | wc -l)
    TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "N/A")
    
    log "========== Redis 백업 상태 리포트 =========="
    log "백업 디렉토리: $BACKUP_DIR"
    log "백업 파일 수: $BACKUP_COUNT"
    log "총 백업 크기: $TOTAL_SIZE"
    log "보관 기간: ${RETENTION_DAYS}일"
    log "최신 백업 세트: ${BACKUP_FILENAME}_*.gz"
    log "=========================================="
}

# 메인 실행 함수
main() {
    log "Redis 백업 스크립트 시작"
    
    setup_backup_dir
    test_redis_connection
    perform_rdb_backup
    perform_aof_backup
    perform_memory_backup
    backup_redis_config
    compress_backups
    verify_backups
    cleanup_old_backups
    generate_report
    
    log "Redis 백업 프로세스 완료"
}

# 스크립트 실행
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi