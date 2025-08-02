#!/bin/bash

# 백업 크론 작업 설정 스크립트
# PostgreSQL과 Redis 백업을 위한 크론 작업을 설정합니다.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 로깅 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 사용법 표시
show_usage() {
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  --install     크론 작업 설치"
    echo "  --uninstall   크론 작업 제거"
    echo "  --status      현재 크론 작업 상태 확인"
    echo "  --help        이 도움말 표시"
}

# 크론 작업 정의
get_cron_jobs() {
    cat << EOF
# KKUA PostgreSQL 백업 - 매일 새벽 2시
0 2 * * * cd ${PROJECT_ROOT} && ${SCRIPT_DIR}/backup_postgres.sh >> ${PROJECT_ROOT}/logs/cron.log 2>&1

# KKUA Redis 백업 - 매일 새벽 3시
0 3 * * * cd ${PROJECT_ROOT} && ${SCRIPT_DIR}/backup_redis.sh >> ${PROJECT_ROOT}/logs/cron.log 2>&1

# 백업 정리 - 매주 일요일 새벽 4시 (30일 이상 된 백업 삭제)
0 4 * * 0 find ${PROJECT_ROOT}/backups -name "*.gz" -mtime +30 -delete >> ${PROJECT_ROOT}/logs/cron.log 2>&1
EOF
}

# 크론 작업 설치
install_cron_jobs() {
    log "크론 작업 설치 중..."
    
    # 로그 디렉토리 생성
    mkdir -p "${PROJECT_ROOT}/logs"
    
    # 기존 KKUA 관련 크론 작업 제거
    crontab -l 2>/dev/null | grep -v "KKUA\|${PROJECT_ROOT}" | crontab - 2>/dev/null || true
    
    # 새로운 크론 작업 추가
    (crontab -l 2>/dev/null || true; get_cron_jobs) | crontab -
    
    log "크론 작업 설치 완료"
    log "설치된 작업:"
    get_cron_jobs | grep -v "^#"
}

# 크론 작업 제거
uninstall_cron_jobs() {
    log "크론 작업 제거 중..."
    
    # KKUA 관련 크론 작업만 제거
    crontab -l 2>/dev/null | grep -v "KKUA\|${PROJECT_ROOT}" | crontab - 2>/dev/null || true
    
    log "크론 작업 제거 완료"
}

# 크론 작업 상태 확인
check_cron_status() {
    log "현재 크론 작업 상태:"
    echo ""
    
    # KKUA 관련 크론 작업 표시
    KKUA_CRONS=$(crontab -l 2>/dev/null | grep "KKUA\|${PROJECT_ROOT}" || true)
    
    if [ -n "$KKUA_CRONS" ]; then
        echo "$KKUA_CRONS"
        echo ""
        log "총 $(echo "$KKUA_CRONS" | wc -l)개의 KKUA 백업 작업이 등록되어 있습니다."
    else
        log "등록된 KKUA 백업 작업이 없습니다."
    fi
    
    # 크론 서비스 상태 확인
    if systemctl is-active --quiet cron 2>/dev/null || systemctl is-active --quiet crond 2>/dev/null; then
        log "크론 서비스가 실행 중입니다."
    else
        log "경고: 크론 서비스가 실행되지 않고 있습니다."
    fi
    
    # 최근 백업 실행 로그 확인
    if [ -f "${PROJECT_ROOT}/logs/cron.log" ]; then
        echo ""
        log "최근 백업 실행 로그 (마지막 5줄):"
        tail -5 "${PROJECT_ROOT}/logs/cron.log" 2>/dev/null || log "로그 파일을 읽을 수 없습니다."
    fi
}

# Docker 환경에서의 크론 설정 가이드
show_docker_guide() {
    cat << EOF

📝 Docker 환경에서의 백업 설정 가이드:

Docker 환경에서는 호스트 시스템에서 크론을 설정하는 것이 권장됩니다.

1. 호스트에서 크론 설정:
   sudo ${SCRIPT_DIR}/setup_backup_cron.sh --install

2. 또는 systemd 타이머 사용 (권장):
   - ${PROJECT_ROOT}/scripts/systemd/ 디렉토리의 서비스 파일 참조

3. Docker Compose에서 백업 서비스 추가:
   docker-compose.yml에 다음 서비스 추가:
   
   backup:
     build: ./backend
     volumes:
       - ./backups:/app/backups
       - ./scripts:/app/scripts
       - ./logs:/app/logs
     environment:
       - DATABASE_HOST=db
       - REDIS_HOST=redis
     depends_on:
       - db
       - redis
     restart: "no"
     profiles: ["backup"]

4. 수동 백업 실행:
   docker-compose --profile backup run --rm backup /app/scripts/backup_postgres.sh

EOF
}

# 테스트 실행
test_backup_scripts() {
    log "백업 스크립트 테스트 실행 중..."
    
    # PostgreSQL 백업 테스트
    if [ -x "${SCRIPT_DIR}/backup_postgres.sh" ]; then
        log "PostgreSQL 백업 스크립트 테스트..."
        "${SCRIPT_DIR}/backup_postgres.sh" || log "PostgreSQL 백업 테스트 실패"
    else
        log "PostgreSQL 백업 스크립트를 찾을 수 없습니다."
    fi
    
    # Redis 백업 테스트 (스크립트가 있을 경우)
    if [ -x "${SCRIPT_DIR}/backup_redis.sh" ]; then
        log "Redis 백업 스크립트 테스트..."
        "${SCRIPT_DIR}/backup_redis.sh" || log "Redis 백업 테스트 실패"
    else
        log "Redis 백업 스크립트를 찾을 수 없습니다."
    fi
    
    log "백업 스크립트 테스트 완료"
}

# 메인 실행 함수
main() {
    case "${1:-}" in
        --install)
            install_cron_jobs
            ;;
        --uninstall)
            uninstall_cron_jobs
            ;;
        --status)
            check_cron_status
            ;;
        --test)
            test_backup_scripts
            ;;
        --docker-guide)
            show_docker_guide
            ;;
        --help|-h)
            show_usage
            ;;
        *)
            show_usage
            echo ""
            log "Docker 환경 가이드를 보려면: $0 --docker-guide"
            exit 1
            ;;
    esac
}

# 스크립트 실행
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi