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
    echo -e "${YELLOW}⚠️  Docker 그룹 권한 적용 중...${NC}"
    # Docker 권한 즉시 적용
    newgrp docker << DOCKERGROUP
    echo "Docker 그룹 적용됨"
DOCKERGROUP
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

# 랜덤 패스워드 생성
DB_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -hex 32)
SECRET_KEY=$(openssl rand -hex 32)

cat > .env << EOF
# Database
DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/kkua_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=kkua_db

# Redis
REDIS_URL=redis://redis:6379

# Security
JWT_SECRET=${JWT_SECRET}
SECRET_KEY=${SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# CORS
CORS_ORIGINS=http://${PUBLIC_IP},http://localhost

# Public IP
PUBLIC_IP=${PUBLIC_IP}
EOF

echo -e "${BLUE}📝 nginx 설정 파일 생성 중...${NC}"
cat > nginx.prod.conf << 'NGINX'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        client_max_body_size 10M;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }

        # Backend API
        location /api {
            rewrite ^/api(.*) $1 break;
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }

        # WebSocket
        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            proxy_pass http://backend/health;
        }
    }
}
NGINX

echo -e "${BLUE}📝 Frontend Dockerfile.prod 확인 중...${NC}"
if [ ! -f frontend/Dockerfile.prod ]; then
    echo -e "${YELLOW}Frontend Dockerfile.prod 생성 중...${NC}"
    cat > frontend/Dockerfile.prod << 'DOCKERFILE'
# Build stage
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
DOCKERFILE
fi

echo -e "${BLUE}🚀 서비스 배포 중...${NC}"
# Docker 권한 문제 해결을 위해 sudo 사용
sudo docker-compose -f config/docker-compose.prod.yml down --volumes --remove-orphans 2>/dev/null || true
sudo docker system prune -af --volumes 2>/dev/null || true
sudo docker-compose -f config/docker-compose.prod.yml build --no-cache
sudo docker-compose -f config/docker-compose.prod.yml up -d

# 서비스 시작 대기
echo -e "${BLUE}⏳ 서비스 시작 대기 중 (30초)...${NC}"
sleep 30

# 헬스 체크
echo -e "${BLUE}🔍 서비스 상태 확인 중...${NC}"
if sudo docker-compose -f config/docker-compose.prod.yml ps | grep -q "Up"; then
    echo -e "${GREEN}✅ 설치 완료!${NC}"
    echo
    echo -e "${GREEN}🎮 게임: http://${PUBLIC_IP}${NC}"
    echo -e "${GREEN}📚 API 문서: http://${PUBLIC_IP}/api/docs${NC}"
    echo -e "${GREEN}❤️  헬스체크: http://${PUBLIC_IP}/health${NC}"
    echo
    echo -e "${YELLOW}📋 서비스 상태 확인:${NC}"
    echo "   sudo docker-compose -f config/docker-compose.prod.yml ps"
    echo
    echo -e "${YELLOW}📋 로그 확인:${NC}"
    echo "   sudo docker-compose -f config/docker-compose.prod.yml logs -f"
    echo
    echo -e "${YELLOW}🔐 환경변수는 .env 파일에 저장되었습니다${NC}"
else
    echo -e "${RED}❌ 배포 실패. 로그를 확인하세요:${NC}"
    sudo docker-compose -f config/docker-compose.prod.yml logs --tail=50
    exit 1
fi