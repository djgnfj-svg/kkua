#!/bin/bash

##################################################
# 끄아(KKUA) V2 - AWS EC2 자동 배포 스크립트
# Docker 설치부터 서비스 실행까지 한 번에!
##################################################

set -e  # 에러 발생시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

log_header() {
    echo -e "${PURPLE}========================================${NC}"
    echo -e "${PURPLE} $1${NC}"
    echo -e "${PURPLE}========================================${NC}"
}

# GitHub URL 검증 함수
validate_github_url() {
    if [[ ! "$1" =~ ^https://github\.com/.+/.+\.git$ ]] && [[ ! "$1" =~ ^https://github\.com/.+/.+$ ]]; then
        return 1
    fi
    return 0
}

# 스크립트 시작
clear
log_header "끄아(KKUA) V2 자동 배포 스크립트"
echo -e "${GREEN}🎮 실시간 멀티플레이어 끝말잇기 게임을 배포합니다!${NC}"
echo ""

# GitHub 저장소 URL 입력받기
while true; do
    echo -e "${YELLOW}GitHub 저장소 URL을 입력하세요:${NC}"
    echo -e "${BLUE}예시: https://github.com/username/kkua.git${NC}"
    echo -e "${BLUE}또는: https://github.com/username/kkua${NC}"
    read -p "GitHub URL: " GITHUB_URL
    
    if [ -z "$GITHUB_URL" ]; then
        log_error "URL을 입력해주세요!"
        continue
    fi
    
    # .git이 없으면 추가
    if [[ ! "$GITHUB_URL" =~ \.git$ ]]; then
        GITHUB_URL="${GITHUB_URL}.git"
    fi
    
    if validate_github_url "$GITHUB_URL"; then
        log_success "유효한 GitHub URL입니다: $GITHUB_URL"
        break
    else
        log_error "올바른 GitHub URL이 아닙니다. 다시 입력해주세요."
        echo -e "${YELLOW}형식: https://github.com/username/repository.git${NC}"
    fi
done

# 브랜치 선택
echo ""
echo -e "${YELLOW}브랜치를 선택하세요 (기본값: main):${NC}"
read -p "브랜치 [main]: " BRANCH
BRANCH=${BRANCH:-main}
log_info "선택된 브랜치: $BRANCH"

# 설치 확인
echo ""
echo -e "${YELLOW}다음 구성요소들이 설치됩니다:${NC}"
echo "  • Docker & Docker Compose"
echo "  • Git"
echo "  • 끄아 게임 서버 (백엔드 + 프론트엔드 + DB)"
echo ""
echo -e "${RED}⚠️  주의: 이 스크립트는 sudo 권한이 필요하며, 시스템을 수정합니다.${NC}"
echo -e "${YELLOW}계속하시겠습니까? (y/N):${NC}"
read -p "" CONFIRM

if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    log_warning "배포를 취소했습니다."
    exit 0
fi

echo ""
log_header "1. 시스템 업데이트"
log_info "시스템 패키지를 업데이트하는 중..."
sudo apt update -qq
sudo apt upgrade -y -qq
log_success "시스템 업데이트 완료"

echo ""
log_header "2. 필수 패키지 설치"
log_info "Git, curl, htop 등을 설치하는 중..."
sudo apt install -y -qq git curl htop unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release
log_success "필수 패키지 설치 완료"

echo ""
log_header "3. Docker 설치"
if command -v docker &> /dev/null; then
    log_warning "Docker가 이미 설치되어 있습니다."
    docker --version
else
    log_info "Docker를 설치하는 중..."
    
    # Docker 공식 GPG 키 추가
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Docker repository 추가
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Docker 설치
    sudo apt update -qq
    sudo apt install -y -qq docker-ce docker-ce-cli containerd.io
    
    log_success "Docker 설치 완료"
    docker --version
fi

echo ""
log_header "4. Docker Compose 설치"
if command -v docker-compose &> /dev/null; then
    log_warning "Docker Compose가 이미 설치되어 있습니다."
    docker-compose --version
else
    log_info "Docker Compose를 설치하는 중..."
    
    # 최신 버전 다운로드
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    log_success "Docker Compose 설치 완료"
    docker-compose --version
fi

echo ""
log_header "5. Docker 권한 설정"
log_info "사용자를 docker 그룹에 추가하는 중..."
sudo usermod -aG docker $USER
log_success "Docker 권한 설정 완료"
log_warning "권한 적용을 위해 잠시 기다리는 중... (5초)"
sleep 5

echo ""
log_header "6. 프로젝트 클론"
PROJECT_DIR="$HOME/kkua"

if [ -d "$PROJECT_DIR" ]; then
    log_warning "프로젝트 디렉토리가 이미 존재합니다: $PROJECT_DIR"
    echo -e "${YELLOW}기존 디렉토리를 삭제하고 다시 클론하시겠습니까? (y/N):${NC}"
    read -p "" REMOVE_CONFIRM
    
    if [[ "$REMOVE_CONFIRM" =~ ^[Yy]$ ]]; then
        log_info "기존 디렉토리 제거 중..."
        rm -rf "$PROJECT_DIR"
    else
        log_info "기존 디렉토리로 이동합니다..."
        cd "$PROJECT_DIR"
        git pull origin "$BRANCH"
    fi
fi

if [ ! -d "$PROJECT_DIR" ]; then
    log_info "GitHub에서 프로젝트를 클론하는 중..."
    log_info "Repository: $GITHUB_URL"
    log_info "Branch: $BRANCH"
    
    git clone -b "$BRANCH" "$GITHUB_URL" "$PROJECT_DIR"
    log_success "프로젝트 클론 완료"
fi

cd "$PROJECT_DIR"
log_info "작업 디렉토리: $(pwd)"

echo ""
log_header "7. 환경 설정"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        log_info ".env.example을 복사하여 .env 파일을 생성합니다..."
        cp .env.example .env
    else
        log_info ".env 파일을 생성합니다..."
        cat > .env << EOF
# 데이터베이스 설정
DATABASE_URL=postgresql://postgres:kkua_password_2024@db:5432/kkua_db

# Redis 설정
REDIS_URL=redis://redis:6379/0

# 보안 설정 (프로덕션에서는 반드시 변경하세요!)
SECRET_KEY=kkua-super-secret-key-change-in-production-$(date +%s)
JWT_SECRET=kkua-jwt-secret-$(date +%s)

# 환경 설정
ENVIRONMENT=production
DEBUG=false

# CORS 설정
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# 프론트엔드 설정
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_DEBUG=false
EOF
    fi
    log_success ".env 파일이 생성되었습니다."
else
    log_warning ".env 파일이 이미 존재합니다."
fi

# EC2 public IP 자동 감지 및 설정
log_info "EC2 public IP를 감지하는 중..."
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")

if [ "$PUBLIC_IP" != "localhost" ]; then
    log_success "EC2 Public IP 감지됨: $PUBLIC_IP"
    
    # .env 파일에서 CORS_ORIGINS와 VITE_*_URL 업데이트
    sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=http://${PUBLIC_IP}:5173,http://${PUBLIC_IP}|g" .env
    sed -i "s|VITE_API_URL=.*|VITE_API_URL=http://${PUBLIC_IP}:8000|g" .env
    sed -i "s|VITE_WS_URL=.*|VITE_WS_URL=ws://${PUBLIC_IP}:8000|g" .env
    
    log_success "환경변수에 Public IP가 자동으로 설정되었습니다."
else
    log_warning "EC2 Public IP를 감지할 수 없습니다. localhost를 사용합니다."
fi

echo ""
log_header "8. Docker 이미지 빌드 및 서비스 시작"
log_info "기존 컨테이너를 중지하고 새로 빌드합니다..."

# 기존 컨테이너 정리
newgrp docker << END_DOCKER
docker-compose down 2>/dev/null || true
END_DOCKER

log_info "Docker 이미지를 빌드하는 중... (시간이 좀 걸릴 수 있습니다)"

# Docker 그룹 권한으로 실행
newgrp docker << END_DOCKER
docker-compose up -d --build
END_DOCKER

log_success "Docker 컨테이너 시작 완료!"

echo ""
log_header "9. 서비스 상태 확인"
sleep 10  # 서비스 시작 대기

log_info "컨테이너 상태를 확인하는 중..."
newgrp docker << END_DOCKER
docker-compose ps
END_DOCKER

# 백엔드 헬스체크
log_info "백엔드 서비스 확인 중..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health &>/dev/null; then
        log_success "✅ 백엔드 서비스가 정상 작동 중입니다!"
        break
    else
        if [ $i -eq 30 ]; then
            log_error "❌ 백엔드 서비스 시작 실패"
            echo -e "${YELLOW}로그를 확인해보세요: docker-compose logs backend${NC}"
        else
            echo -n "."
            sleep 2
        fi
    fi
done

echo ""
log_header "10. 스왑 메모리 설정 (메모리 부족 방지)"
if [ ! -f /swapfile ]; then
    log_info "2GB 스왑 파일을 생성하는 중..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    log_success "스왑 메모리 설정 완료"
else
    log_warning "스왑 파일이 이미 존재합니다."
fi

echo ""
log_header "🎉 배포 완료!"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN} 끄아(KKUA) V2 배포 성공! 🎮${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}📍 접속 정보:${NC}"
if [ "$PUBLIC_IP" != "localhost" ]; then
    echo -e "   🎮 게임 페이지:    ${BLUE}http://${PUBLIC_IP}:5173${NC}"
    echo -e "   📚 API 문서:       ${BLUE}http://${PUBLIC_IP}:8000/docs${NC}"
    echo -e "   ❤️  헬스체크:      ${BLUE}http://${PUBLIC_IP}:8000/health${NC}"
else
    echo -e "   🎮 게임 페이지:    ${BLUE}http://localhost:5173${NC}"
    echo -e "   📚 API 문서:       ${BLUE}http://localhost:8000/docs${NC}"
    echo -e "   ❤️  헬스체크:      ${BLUE}http://localhost:8000/health${NC}"
fi

echo ""
echo -e "${YELLOW}🔧 유용한 명령어:${NC}"
echo -e "   로그 확인:         ${BLUE}docker-compose logs -f${NC}"
echo -e "   서비스 재시작:     ${BLUE}docker-compose restart${NC}"
echo -e "   서비스 중지:       ${BLUE}docker-compose down${NC}"
echo -e "   시스템 모니터링:   ${BLUE}htop${NC}"

echo ""
echo -e "${YELLOW}📁 프로젝트 경로:${NC} ${BLUE}$PROJECT_DIR${NC}"
echo ""
echo -e "${GREEN}🎈 Happy Gaming! 끝말잇기를 즐겨보세요!${NC}"

# 자동 시작 서비스 등록 여부 확인
echo ""
echo -e "${YELLOW}시스템 재부팅시 자동으로 서비스를 시작하시겠습니까? (y/N):${NC}"
read -p "" AUTO_START

if [[ "$AUTO_START" =~ ^[Yy]$ ]]; then
    log_info "자동 시작 서비스를 등록하는 중..."
    
    sudo tee /etc/systemd/system/kkua.service > /dev/null << EOF
[Unit]
Description=KKUA Game Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl enable kkua.service
    log_success "자동 시작 서비스가 등록되었습니다!"
fi

echo ""
log_success "모든 배포 작업이 완료되었습니다! 🚀"

exit 0