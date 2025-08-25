#!/bin/bash

set -euo pipefail

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수들
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 배너 출력
print_banner() {
    echo -e "${BLUE}"
    echo "================================================"
    echo "         끄아(KKUA) V2 EC2 배포 스크립트"
    echo "     실시간 멀티플레이어 한국어 끝말잇기 게임"
    echo "================================================"
    echo -e "${NC}"
}

# 시스템 요구사항 확인
check_system_requirements() {
    log_info "시스템 요구사항 확인 중..."
    
    # OS 확인
    if [[ ! -f /etc/os-release ]]; then
        log_error "지원하지 않는 운영체제입니다."
        exit 1
    fi
    
    source /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        log_error "Ubuntu 운영체제만 지원됩니다. 현재 OS: $ID"
        exit 1
    fi
    
    log_success "Ubuntu $VERSION_ID 확인됨"
    
    # 메모리 확인
    MEMORY=$(free -m | awk 'NR==2{printf "%.0f", $2/1024}')
    if [[ $MEMORY -lt 1 ]]; then
        log_warning "메모리가 부족합니다. 최소 1GB 권장 (현재: ${MEMORY}GB)"
        log_info "스왑 메모리를 설정합니다..."
        setup_swap
    else
        log_success "메모리 확인됨: ${MEMORY}GB"
    fi
    
    # 디스크 확인
    DISK=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $DISK -lt 10 ]]; then
        log_error "디스크 공간이 부족합니다. 최소 10GB 필요 (현재: ${DISK}GB)"
        exit 1
    fi
    
    log_success "디스크 공간 확인됨: ${DISK}GB"
}

# 스왑 메모리 설정
setup_swap() {
    if [[ ! -f /swapfile ]]; then
        log_info "2GB 스왑 메모리 생성 중..."
        sudo fallocate -l 2G /swapfile
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
        log_success "스왑 메모리 설정 완료"
    else
        log_info "스왑 메모리가 이미 설정되어 있습니다."
    fi
}

# Docker 설치
install_docker() {
    if ! command -v docker &> /dev/null; then
        log_info "Docker 설치 중..."
        
        # 기존 Docker 제거
        sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
        
        # 의존성 설치
        sudo apt-get update
        sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
        
        # Docker GPG 키 추가
        sudo mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        
        # Docker 저장소 추가
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Docker 설치
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        
        # Docker 서비스 시작
        sudo systemctl start docker
        sudo systemctl enable docker
        
        # 현재 사용자를 docker 그룹에 추가
        sudo usermod -aG docker $USER
        
        log_success "Docker 설치 완료"
    else
        log_info "Docker가 이미 설치되어 있습니다."
    fi
}

# 프로젝트 클론 또는 업데이트
setup_project() {
    local repo_url="${1:-https://github.com/djgnfj-svg/kkua.git}"
    local project_dir="/opt/kkua"
    
    if [[ -d "$project_dir" ]]; then
        log_info "기존 프로젝트 업데이트 중..."
        cd "$project_dir"
        git pull origin main || git pull origin develop
    else
        log_info "프로젝트 클론 중..."
        sudo mkdir -p /opt
        sudo git clone "$repo_url" "$project_dir"
        sudo chown -R $USER:$USER "$project_dir"
    fi
    
    cd "$project_dir"
    log_success "프로젝트 설정 완료: $project_dir"
}

# 환경변수 설정
setup_environment() {
    local env_file=".env"
    
    if [[ -f "$env_file" ]]; then
        log_warning "기존 .env 파일이 있습니다. 백업 후 새로 생성합니다."
        cp "$env_file" "${env_file}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    log_info "환경변수 설정 중..."
    
    # 기본값들
    local postgres_password=""
    local secret_key=""
    local jwt_secret=""
    local domain=""
    
    # 사용자 입력 받기
    echo -n -e "${YELLOW}PostgreSQL 비밀번호를 입력하세요: ${NC}"
    read -s postgres_password
    echo
    
    echo -n -e "${YELLOW}SECRET_KEY를 입력하세요 (비워두면 자동 생성): ${NC}"
    read secret_key
    if [[ -z "$secret_key" ]]; then
        secret_key=$(openssl rand -hex 32)
        log_info "SECRET_KEY 자동 생성됨"
    fi
    
    echo -n -e "${YELLOW}JWT_SECRET을 입력하세요 (비워두면 자동 생성): ${NC}"
    read jwt_secret
    if [[ -z "$jwt_secret" ]]; then
        jwt_secret=$(openssl rand -hex 32)
        log_info "JWT_SECRET 자동 생성됨"
    fi
    
    echo -n -e "${YELLOW}도메인을 입력하세요 (예: example.com, 비워두면 IP 사용): ${NC}"
    read domain
    
    # EC2 Public IP 자동 감지
    local public_ip
    public_ip=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")
    
    # CORS 설정
    local cors_origins="http://localhost:3000,http://${public_ip}"
    if [[ -n "$domain" ]]; then
        cors_origins="${cors_origins},http://${domain},https://${domain}"
    fi
    
    # .env 파일 생성
    cat > "$env_file" << EOF
# 데이터베이스 설정
POSTGRES_DB=kkua_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${postgres_password}

# 애플리케이션 보안 키
SECRET_KEY=${secret_key}
JWT_SECRET=${jwt_secret}

# CORS 설정
CORS_ORIGINS=${cors_origins}

# 서버 정보 (자동 감지됨)
PUBLIC_IP=${public_ip}
DOMAIN=${domain}

# 생성 시간
CREATED_AT=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
EOF
    
    chmod 600 "$env_file"
    log_success "환경변수 설정 완료"
    log_info "Public IP: ${public_ip}"
    if [[ -n "$domain" ]]; then
        log_info "도메인: ${domain}"
    fi
}

# 프로덕션 빌드 및 배포
deploy_application() {
    log_info "애플리케이션 빌드 및 배포 중..."
    
    # 기존 컨테이너 정지 및 제거
    if docker compose -f docker-compose.prod.yml ps -q | grep -q .; then
        log_info "기존 서비스 중지 중..."
        docker compose -f docker-compose.prod.yml down --volumes --remove-orphans
    fi
    
    # 이미지 빌드
    log_info "Docker 이미지 빌드 중... (시간이 걸릴 수 있습니다)"
    docker compose -f docker-compose.prod.yml build --no-cache
    
    # 서비스 시작
    log_info "서비스 시작 중..."
    docker compose -f docker-compose.prod.yml up -d
    
    log_success "배포 완료!"
}

# 서비스 상태 확인
check_services() {
    log_info "서비스 상태 확인 중..."
    
    # 컨테이너 상태 확인
    sleep 10
    
    local services=("kkua-nginx" "kkua-backend" "kkua-frontend" "kkua-db" "kkua-redis")
    local all_healthy=true
    
    for service in "${services[@]}"; do
        if docker ps --filter "name=$service" --filter "status=running" | grep -q "$service"; then
            log_success "$service: 실행 중"
        else
            log_error "$service: 실행되지 않음"
            all_healthy=false
        fi
    done
    
    # 헬스체크
    local public_ip
    public_ip=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")
    
    log_info "헬스체크 수행 중..."
    if curl -f -s "http://localhost/health" > /dev/null; then
        log_success "웹 서비스: 정상"
    else
        log_error "웹 서비스: 응답 없음"
        all_healthy=false
    fi
    
    if $all_healthy; then
        log_success "모든 서비스가 정상적으로 실행 중입니다!"
        echo -e "${GREEN}"
        echo "================================================"
        echo "           🎮 배포 완료! 🎮"
        echo "================================================"
        echo "게임 URL: http://${public_ip}"
        echo "API 문서: http://${public_ip}/docs"
        echo "헬스체크: http://${public_ip}/health"
        echo "================================================"
        echo -e "${NC}"
    else
        log_error "일부 서비스에 문제가 있습니다. 로그를 확인하세요:"
        echo "docker compose -f docker-compose.prod.yml logs"
    fi
}

# 방화벽 설정
setup_firewall() {
    log_info "방화벽 설정 중..."
    
    # UFW 활성화 (이미 활성화된 경우 무시)
    echo 'y' | sudo ufw enable 2>/dev/null || true
    
    # 필요한 포트 열기
    sudo ufw allow 22/tcp      # SSH
    sudo ufw allow 80/tcp      # HTTP
    sudo ufw allow 443/tcp     # HTTPS
    
    log_success "방화벽 설정 완료"
}

# 자동 시작 서비스 등록
setup_systemd_service() {
    log_info "자동 시작 서비스 설정 중..."
    
    local service_file="/etc/systemd/system/kkua.service"
    local project_dir="/opt/kkua"
    
    sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=KKUA Game Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${project_dir}
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable kkua.service
    
    log_success "자동 시작 서비스 등록 완료"
}

# 로그 로테이션 설정
setup_log_rotation() {
    log_info "로그 로테이션 설정 중..."
    
    sudo tee /etc/logrotate.d/kkua > /dev/null << 'EOF'
/opt/kkua/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 ubuntu ubuntu
    postrotate
        docker kill --signal="USR1" kkua-backend 2>/dev/null || true
    endscript
}
EOF
    
    # 로그 디렉토리 생성
    mkdir -p /opt/kkua/logs
    
    log_success "로그 로테이션 설정 완료"
}

# 메인 함수
main() {
    print_banner
    
    # 매개변수 확인
    local repo_url="${1:-}"
    if [[ -z "$repo_url" ]]; then
        echo -n -e "${YELLOW}GitHub 저장소 URL을 입력하세요 (기본값: https://github.com/djgnfj-svg/kkua.git): ${NC}"
        read repo_url
    fi
    
    log_info "배포를 시작합니다..."
    
    # 설치 단계들
    check_system_requirements
    install_docker
    setup_project "$repo_url"
    setup_environment
    setup_firewall
    deploy_application
    setup_systemd_service
    setup_log_rotation
    check_services
    
    log_success "🎉 끄아(KKUA) V2 배포가 완료되었습니다!"
    log_info "문제가 발생하면 다음 명령어로 로그를 확인하세요:"
    echo "  docker compose -f /opt/kkua/docker-compose.prod.yml logs -f"
}

# 에러 핸들링
error_handler() {
    log_error "스크립트 실행 중 오류가 발생했습니다. (라인 $1)"
    log_info "문제 해결을 위해 로그를 확인하고 다시 실행해 주세요."
    exit 1
}

trap 'error_handler $LINENO' ERR

# 스크립트 실행
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi