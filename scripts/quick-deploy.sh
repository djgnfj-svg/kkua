#!/bin/bash

# 빠른 배포 스크립트 - 이미 설정된 환경에서 재배포
set -euo pipefail

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

# 현재 디렉토리가 프로젝트 루트인지 확인
if [[ ! -f "docker-compose.prod.yml" ]]; then
    log_error "docker-compose.prod.yml 파일을 찾을 수 없습니다."
    log_info "프로젝트 루트 디렉토리에서 실행해주세요."
    exit 1
fi

log_info "빠른 재배포를 시작합니다..."

# 1. 최신 코드 가져오기
log_info "최신 코드 가져오는 중..."
git pull origin $(git branch --show-current)

# 2. 서비스 중지
log_info "기존 서비스 중지 중..."
docker compose -f docker-compose.prod.yml down

# 3. 이미지 재빌드 (캐시 사용)
log_info "이미지 빌드 중..."
docker compose -f docker-compose.prod.yml build

# 4. 서비스 시작
log_info "서비스 시작 중..."
docker compose -f docker-compose.prod.yml up -d

# 5. 서비스 상태 확인
log_info "서비스 상태 확인 중..."
sleep 10

if curl -f -s http://localhost/health > /dev/null; then
    log_success "재배포 완료! 서비스가 정상적으로 실행 중입니다."
    
    # Public IP 확인
    public_ip=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")
    echo "게임 URL: http://${public_ip}"
else
    log_error "서비스가 정상적으로 시작되지 않았습니다."
    log_info "로그를 확인하세요: docker compose -f docker-compose.prod.yml logs"
    exit 1
fi