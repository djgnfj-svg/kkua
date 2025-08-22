# 끄아(KKUA) V2 - AWS EC2 간단 배포 가이드

AWS EC2 하나의 인스턴스에서 Docker로 전체 스택을 배포하는 가이드입니다.

## 🚀 빠른 배포

### 1단계: EC2 인스턴스 생성
1. **AWS Console** → **EC2** → **인스턴스 시작**
2. **AMI**: Ubuntu Server 22.04 LTS
3. **인스턴스 유형**: t3.small (권장) 또는 t3.micro
4. **키 페어**: 새로 생성하거나 기존 사용
5. **보안 그룹 설정**:
   ```
   SSH (22)      - 내 IP
   HTTP (80)     - 0.0.0.0/0
   HTTPS (443)   - 0.0.0.0/0  
   Custom (8000) - 0.0.0.0/0  [백엔드 API용]
   Custom (5173) - 0.0.0.0/0  [프론트엔드용, 개발시만]
   ```
6. **스토리지**: 20GB (gp3)

### 2단계: EC2 접속
```bash
# 키 파일 권한 설정
chmod 400 your-key.pem

# EC2 접속
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### 3단계: 자동 배포 스크립트 실행
```bash
# 배포 스크립트 다운로드
curl -o deploy.sh https://raw.githubusercontent.com/YOUR_USERNAME/kkua/develop/deploy.sh

# 실행 권한 부여
chmod +x deploy.sh

# 배포 실행 (GitHub 저장소 URL 입력)
./deploy.sh https://github.com/YOUR_USERNAME/kkua.git
```

## 📋 수동 배포 (스크립트 사용 안할 경우)

### 1. Docker 설치
```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 사용자를 docker 그룹에 추가
sudo usermod -aG docker ubuntu
newgrp docker

# 설치 확인
docker --version
docker-compose --version
```

### 2. 프로젝트 클론 및 실행
```bash
# Git 설치
sudo apt install git -y

# 프로젝트 클론
git clone https://github.com/YOUR_USERNAME/kkua.git
cd kkua

# 환경변수 설정
cp .env.example .env
nano .env  # 필요한 값들 수정

# 빌드 및 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f
```

### 3. 서비스 확인
```bash
# 컨테이너 상태 확인
docker-compose ps

# 백엔드 API 테스트
curl http://localhost:8000/health

# 프론트엔드 접속
# http://YOUR_EC2_PUBLIC_IP:5173
```

## 🔧 환경변수 설정 (.env)

```bash
# 데이터베이스 설정
DATABASE_URL=postgresql://postgres:your_secure_password@db:5432/kkua_db

# Redis 설정  
REDIS_URL=redis://redis:6379/0

# 보안 설정
SECRET_KEY=your-super-secret-key-change-this
JWT_SECRET=your-jwt-secret-key

# 환경 설정
ENVIRONMENT=production
DEBUG=false

# CORS 설정 (EC2 공인 IP로 변경)
CORS_ORIGINS=http://YOUR_EC2_PUBLIC_IP:5173,http://YOUR_EC2_PUBLIC_IP

# 프론트엔드 설정
VITE_API_URL=http://YOUR_EC2_PUBLIC_IP:8000
VITE_WS_URL=ws://YOUR_EC2_PUBLIC_IP:8000
```

## 🛡️ SSL 설정 (선택사항)

### Nginx + Let's Encrypt
```bash
# Nginx 설치
sudo apt install nginx certbot python3-certbot-nginx -y

# 도메인 설정 (your-domain.com으로 가정)
sudo nano /etc/nginx/sites-available/kkua

# SSL 인증서 발급
sudo certbot --nginx -d your-domain.com

# Nginx 재시작
sudo systemctl restart nginx
```

### Nginx 설정 예시 (/etc/nginx/sites-available/kkua)
```nginx
server {
    server_name your-domain.com;
    
    # 프론트엔드 (정적 파일)
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # 백엔드 API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket
    location /ws/ {
        proxy_pass http://localhost:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔍 모니터링 및 관리

### 유용한 명령어
```bash
# 서비스 상태 확인
docker-compose ps
docker-compose logs backend
docker-compose logs frontend

# 서비스 재시작
docker-compose restart backend
docker-compose restart frontend

# 전체 재시작
docker-compose down && docker-compose up -d

# 시스템 리소스 확인
htop
df -h
docker system df
```

### 백업 설정
```bash
# PostgreSQL 백업
docker exec kkua-db-1 pg_dump -U postgres kkua_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 백업 자동화 (crontab)
crontab -e
# 매일 오전 3시 백업
0 3 * * * /home/ubuntu/backup.sh
```

## 🚨 문제 해결

### 1. 포트 충돌
```bash
# 포트 사용 확인
sudo netstat -tlnp | grep :8000
sudo lsof -i :5173

# 프로세스 종료
sudo kill -9 PID
```

### 2. Docker 권한 문제
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### 3. 메모리 부족
```bash
# 스왑 메모리 추가
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 4. 디스크 공간 부족
```bash
# Docker 정리
docker system prune -a
docker volume prune

# 로그 정리
sudo journalctl --vacuum-time=3d
```

## 💰 비용 최적화

### EC2 인스턴스 타입별 월 비용 (미국 동부 기준)
- **t3.micro**: $8.5/월 (1GB RAM) - 최소 사양
- **t3.small**: $17/월 (2GB RAM) - 권장 사양
- **t3.medium**: $34/월 (4GB RAM) - 트래픽 많을 때

### 추가 비용
- **EBS 스토리지**: $2/월 (20GB gp3)
- **데이터 전송**: 월 15GB 무료, 이후 $0.09/GB
- **Elastic IP**: $0 (인스턴스에 연결시), $3.65/월 (미사용시)

## 📈 성능 최적화

### 1. 프로덕션 설정
```yaml
# docker-compose.yml에서
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '0.7'
          memory: 512M
  frontend:
    deploy:
      resources:
        limits:
          memory: 256M
```

### 2. DB 튜닝
```bash
# PostgreSQL 설정 최적화
docker exec -it kkua-db-1 bash
# postgresql.conf 수정
shared_buffers = 128MB
effective_cache_size = 512MB
```

## 🔄 자동 재시작 설정

```bash
# 시스템 재부팅시 자동 시작
sudo nano /etc/systemd/system/kkua.service

[Unit]
Description=KKUA Game Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/kkua
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target

# 서비스 활성화
sudo systemctl enable kkua.service
sudo systemctl start kkua.service
```

## 📞 지원 및 문의

배포 중 문제가 발생하면:
1. **로그 확인**: `docker-compose logs -f`
2. **이슈 등록**: GitHub Issues
3. **문서 참고**: README.md, CLAUDE.md

---

**🎮 배포 완료 후 접속:**
- 게임: `http://YOUR_EC2_PUBLIC_IP:5173`
- API 문서: `http://YOUR_EC2_PUBLIC_IP:8000/docs`

**Happy Gaming! 🎉**