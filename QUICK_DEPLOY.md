# KKUA EC2 배포 가이드

## Step 1: EC2 보안 그룹 설정
포트 80, 8000, 5173, 22 인바운드 허용

## Step 2: 터미널에서 복붙 (순서대로)

### 1. Docker 설치 + 프로젝트 클론
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo systemctl start docker
sudo systemctl enable docker
git clone https://github.com/djgnfj-svg/kkua.git
cd kkua
```

### 2. 환경 파일 생성 (개발 모드 - TypeScript 빌드 에러 우회)
```bash
cat > .env.dev << EOF
ENVIRONMENT=development
DEBUG=true
BACKEND_PORT=8000
FRONTEND_PORT=5173
NGINX_PORT=80
POSTGRES_DB=kkua_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=kkua123
DATABASE_URL=postgresql://postgres:kkua123@db:5432/kkua_db
REDIS_URL=redis://redis:6379/0
SECRET_KEY=test-secret-key
JWT_SECRET=test-jwt-secret
CORS_ORIGINS=http://13.125.132.65:5173,http://localhost:5173
VITE_API_URL=http://13.125.132.65:8000
VITE_WS_URL=ws://13.125.132.65:8000
VITE_NODE_ENV=development
VITE_DEBUG=true
VITE_GAME_TIMER_DURATION=30000
VITE_RECONNECT_INTERVAL=3000
VITE_MAX_RECONNECT_ATTEMPTS=5
SSL_CERT_PATH=
SSL_KEY_PATH=
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
ENABLE_MONITORING=false
LOG_LEVEL=DEBUG
TZ=Asia/Seoul
COMPOSE_PROFILES=
EOF
```

### 3. 개발 모드로 배포
```bash
chmod +x dev.sh
sudo ./dev.sh
```

## Step 3: 접속 테스트

- **🎮 게임**: http://13.125.132.65:5173
- **📚 API**: http://13.125.132.65:8000/docs 
- **❤️ 상태**: http://13.125.132.65:8000/health

## 문제 해결

### 상태 확인
```bash
sudo docker ps
sudo docker-compose logs -f
cat .env.dev
```

### 서비스 재시작
```bash
sudo docker-compose restart
sudo docker-compose down && sudo ./dev.sh
```

### IP 확인
```bash
curl -s http://169.254.169.254/latest/meta-data/public-ipv4
```