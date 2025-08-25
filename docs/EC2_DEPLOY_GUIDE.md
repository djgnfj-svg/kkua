# EC2 배포 가이드 - 끄아(KKUA) V2

## 📋 EC2 인스턴스 설정

### 1. EC2 인스턴스 생성
```
- AMI: Ubuntu Server 22.04 LTS
- 인스턴스 타입: t3.small (최소 t3.micro)
- 스토리지: 20GB gp3
- 키 페어: 생성 또는 기존 키 사용
```

### 2. 보안 그룹 설정
```
포트 80 (HTTP) - 0.0.0.0/0
포트 443 (HTTPS) - 0.0.0.0/0  
포트 22 (SSH) - 내 IP
포트 8000 (API) - 0.0.0.0/0 (선택사항)
```

## 🚀 배포 단계

### Step 1: EC2 접속
```bash
# 키 파일 권한 설정
chmod 400 your-key.pem

# EC2 접속
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### Step 2: 시스템 업데이트
```bash
sudo apt update
sudo apt upgrade -y
```

### Step 3: Docker 설치
```bash
# Docker 공식 저장소 추가
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker 설치
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# 재로그인 (또는 재부팅)
exit
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### Step 4: Docker Compose 설치
```bash
# Docker Compose 최신 버전 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

sudo chmod +x /usr/local/bin/docker-compose

# 설치 확인
docker --version
docker-compose --version
```

### Step 5: 프로젝트 클론
```bash
# Git 설치
sudo apt install -y git

# 프로젝트 클론
git clone https://github.com/YOUR_USERNAME/kkua.git
cd kkua
```

### Step 6: 환경변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# EC2 Public IP 확인
curl -s http://169.254.169.254/latest/meta-data/public-ipv4

# .env 파일 편집
nano .env
```

### Step 7: 환경변수 예시
```env
# Database
DATABASE_URL=postgresql://postgres:password@db:5432/kkua_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=kkua_db

# Redis
REDIS_URL=redis://redis:6379

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-here-make-it-long-and-random
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Frontend (EC2 Public IP로 변경)
VITE_API_URL=http://YOUR_EC2_PUBLIC_IP/api
VITE_WS_URL=ws://YOUR_EC2_PUBLIC_IP/api
```

### Step 8: 메모리 스왑 설정 (t3.micro/small용)
```bash
# 2GB 스왑 파일 생성
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 영구 설정
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 확인
free -h
```

### Step 9: 배포 실행
```bash
# 실행 권한 부여
chmod +x quick-deploy.sh

# 배포 실행
./quick-deploy.sh
```

### Step 10: 서비스 확인
```bash
# 컨테이너 상태 확인
docker-compose -f docker-compose.prod.yml ps

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f

# 헬스체크
curl http://localhost/api/health
```

## 🔧 문제 해결

### 메모리 부족
```bash
# 현재 메모리 사용량 확인
free -h
htop

# 더 큰 스왑 추가
sudo swapoff /swapfile
sudo fallocate -l 4G /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 포트 충돌
```bash
# 포트 사용 확인
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443

# 충돌 서비스 중지
sudo systemctl stop apache2
sudo systemctl stop nginx
```

### Docker 권한 문제
```bash
# Docker 그룹 확인
groups $USER

# 다시 로그인
exit
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

## 🔄 업데이트

### 코드 업데이트
```bash
cd kkua
git pull origin develop
./quick-deploy.sh
```

### 데이터만 유지하고 업데이트
```bash
# 컨테이너만 중지 (볼륨 유지)
docker-compose -f docker-compose.prod.yml down

# 새 코드로 재빌드
docker-compose -f docker-compose.prod.yml build --no-cache

# 재시작
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 모니터링

### 리소스 모니터링
```bash
# 시스템 리소스
htop
df -h

# Docker 리소스
docker stats

# 디스크 사용량
docker system df
```

### 로그 모니터링
```bash
# 실시간 로그
docker-compose -f docker-compose.prod.yml logs -f

# 특정 서비스 로그
docker-compose -f docker-compose.prod.yml logs backend --tail=100
```

## 🛡️ 보안

### 방화벽 설정
```bash
# UFW 활성화
sudo ufw enable

# 필요한 포트만 허용
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443

# 상태 확인
sudo ufw status
```

### SSL 인증서 (선택사항)
```bash
# Let's Encrypt 설치
sudo apt install -y certbot python3-certbot-nginx

# 인증서 발급 (도메인 필요)
sudo certbot --nginx -d your-domain.com
```

## 🚨 백업

### 데이터베이스 백업
```bash
# 백업 생성
docker exec kkua-db pg_dump -U postgres kkua_db > backup.sql

# 복원
docker exec -i kkua-db psql -U postgres kkua_db < backup.sql
```

---

**🎮 배포 완료 후 접속:**
- **게임**: http://YOUR_EC2_PUBLIC_IP
- **API 문서**: http://YOUR_EC2_PUBLIC_IP/api/docs