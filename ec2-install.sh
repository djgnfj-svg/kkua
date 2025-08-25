#!/bin/bash

set -e

# 색상 설정
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 끄아(KKUA) V2 EC2 간단 설치${NC}"
echo

# GitHub 설정
GITHUB_URL="https://github.com/djgnfj-svg/kkua"

# Private 저장소인 경우 토큰 입력
echo -n -e "${YELLOW}GitHub Personal Access Token을 입력하세요 (Public이면 Enter): ${NC}"
read -s GITHUB_TOKEN
echo

if [[ -n "$GITHUB_TOKEN" ]]; then
    # URL에 토큰 포함
    GITHUB_URL="https://$GITHUB_TOKEN@github.com/djgnfj-svg/kkua"
fi

echo -e "${BLUE}📦 시스템 업데이트 중...${NC}"
sudo apt update && sudo apt upgrade -y

echo -e "${BLUE}🐳 Docker 설치 중...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    sudo systemctl start docker
    sudo systemctl enable docker
fi

echo -e "${BLUE}🔧 Docker Compose 설치 중...${NC}"
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

echo -e "${BLUE}📂 프로젝트 클론 중...${NC}"
rm -rf kkua 2>/dev/null || true
git clone "$GITHUB_URL"
cd kkua

echo -e "${BLUE}🔑 환경변수 설정 중...${NC}"
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")

cat > .env << EOF
DATABASE_URL=postgresql://postgres:password@db:5432/kkua_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=kkua_db
REDIS_URL=redis://redis:6379
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
PUBLIC_IP=${PUBLIC_IP}
EOF

echo -e "${BLUE}🚀 서비스 배포 중...${NC}"
chmod +x quick-deploy.sh
./quick-deploy.sh

echo -e "${GREEN}✅ 설치 완료!${NC}"
echo -e "${GREEN}🎮 게임: http://${PUBLIC_IP}${NC}"
echo -e "${GREEN}📚 API: http://${PUBLIC_IP}/api/docs${NC}"