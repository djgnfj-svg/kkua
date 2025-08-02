#!/bin/bash

# systemd 백업 서비스 설정 스크립트

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# 로깅 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 에러 처리 함수
error_exit() {
    log "ERROR: $1"
    exit 1
}

# 권한 확인
check_permissions() {
    if [ "$EUID" -ne 0 ]; then
        error_exit "이 스크립트는 root 권한으로 실행해야 합니다."
    fi
}

# 설치 위치 확인 및 생성
setup_installation() {
    INSTALL_PATH="/opt/kkua"
    
    log "설치 경로 설정: $INSTALL_PATH"
    
    # 설치 디렉토리가 없으면 생성
    if [ ! -d "$INSTALL_PATH" ]; then
        mkdir -p "$INSTALL_PATH"
        log "설치 디렉토리 생성: $INSTALL_PATH"
    fi
    
    # 필요한 하위 디렉토리 생성
    mkdir -p "$INSTALL_PATH"/{scripts,backups,logs,backend}
    
    # 스크립트 파일 복사
    cp "${PROJECT_ROOT}/scripts/"*.sh "$INSTALL_PATH/scripts/"
    chmod +x "$INSTALL_PATH/scripts/"*.sh
    
    # 환경설정 파일 복사 (존재하는 경우)
    if [ -f "${PROJECT_ROOT}/backend/.env" ]; then
        cp "${PROJECT_ROOT}/backend/.env" "$INSTALL_PATH/backend/"
        log "환경설정 파일 복사 완료"
    else
        log "경고: .env 파일을 찾을 수 없습니다. 수동으로 설정해주세요."
    fi
}

# systemd 서비스 설치
install_systemd_services() {
    log "systemd 서비스 설치 중..."
    
    # 서비스 파일 복사
    cp "$SCRIPT_DIR"/*.service /etc/systemd/system/
    cp "$SCRIPT_DIR"/*.timer /etc/systemd/system/
    
    # systemd 다시 로드
    systemctl daemon-reload
    
    # 타이머 활성화 및 시작
    systemctl enable kkua-postgres-backup.timer
    systemctl start kkua-postgres-backup.timer
    
    log "systemd 서비스 설치 완료"
}

# systemd 서비스 제거
uninstall_systemd_services() {
    log "systemd 서비스 제거 중..."
    
    # 타이머 정지 및 비활성화
    systemctl stop kkua-postgres-backup.timer 2>/dev/null || true
    systemctl disable kkua-postgres-backup.timer 2>/dev/null || true
    
    # 서비스 파일 삭제
    rm -f /etc/systemd/system/kkua-postgres-backup.service
    rm -f /etc/systemd/system/kkua-postgres-backup.timer
    
    # systemd 다시 로드
    systemctl daemon-reload
    systemctl reset-failed
    
    log "systemd 서비스 제거 완료"
}

# 서비스 상태 확인
check_service_status() {
    log "백업 서비스 상태 확인:"
    echo ""
    
    # 타이머 상태
    log "타이머 상태:"
    systemctl status kkua-postgres-backup.timer --no-pager -l || true
    echo ""
    
    # 다음 실행 시간
    log "다음 백업 예정 시간:"
    systemctl list-timers kkua-postgres-backup.timer --no-pager || true
    echo ""
    
    # 최근 실행 로그
    log "최근 백업 실행 로그:"
    journalctl -u kkua-postgres-backup.service --no-pager -n 10 || true
}

# 수동 백업 실행
run_manual_backup() {
    log "수동 백업 실행 중..."
    
    systemctl start kkua-postgres-backup.service
    
    log "백업 실행 완료. 상태 확인:"
    systemctl status kkua-postgres-backup.service --no-pager -l
}

# 사용법 표시
show_usage() {
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  install      systemd 백업 서비스 설치"
    echo "  uninstall    systemd 백업 서비스 제거"
    echo "  status       백업 서비스 상태 확인"
    echo "  run          수동 백업 실행"
    echo "  help         이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  sudo $0 install    # 백업 서비스 설치"
    echo "  sudo $0 status     # 상태 확인"
    echo "  sudo $0 run        # 수동 백업 실행"
}

# 메인 실행 함수
main() {
    case "${1:-}" in
        install)
            check_permissions
            setup_installation
            install_systemd_services
            log "설치 완료! 'sudo $0 status' 명령으로 상태를 확인하세요."
            ;;
        uninstall)
            check_permissions
            uninstall_systemd_services
            log "제거 완료!"
            ;;
        status)
            check_service_status
            ;;
        run)
            check_permissions
            run_manual_backup
            ;;
        help|-h|--help)
            show_usage
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# 스크립트 실행
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi