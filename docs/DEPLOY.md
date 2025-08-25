# 끄아(KKUA) V2 배포 가이드 🎮

## 📋 목차
- [빠른 시작 (원클릭 배포)](#빠른-시작-원클릭-배포)
- [수동 배포](#수동-배포)
- [환경변수 설정](#환경변수-설정)
- [배포 후 확인](#배포-후-확인)
- [문제 해결](#문제-해결)
- [관리 명령어](#관리-명령어)

## 🚀 빠른 시작 (원클릭 배포)

AWS EC2 Ubuntu 인스턴스에서 **단 한 줄**로 전체 서비스를 배포할 수 있습니다:

```bash
curl -fsSL https://raw.githubusercontent.com/djgnfj-svg/kkua/develop/deploy.sh | bash -s -- https://github.com/djgnfj-svg/kkua.git
```

또는 파일을 다운로드 후 실행:

```bash
wget https://raw.githubusercontent.com/djgnfj-svg/kkua/develop/deploy.sh
chmod +x deploy.sh
./deploy.sh https://github.com/djgnfj-svg/kkua.git
```

### 📋 EC2 인스턴스 요구사항

| 항목 | 최소 사양 | 권장 사양 |
|------|----------|----------|
| **AMI** | Ubuntu Server 22.04 LTS | Ubuntu Server 22.04 LTS |
| **인스턴스 타입** | t3.micro (1GB RAM) | t3.small (2GB RAM) |
| **스토리지** | 15GB gp3 | 20GB gp3 |
| **보안 그룹** | 포트 22, 80, 443 오픈 | 포트 22, 80, 443 오픈 |

### 🔧 자동으로 처리되는 것들

- ✅ Docker & Docker Compose 설치
- ✅ 시스템 요구사항 확인 및 스왑 메모리 설정
- ✅ GitHub에서 프로젝트 클론
- ✅ 환경변수 자동/수동 설정
- ✅ EC2 Public IP 자동 감지
- ✅ 프로덕션 빌드 및 배포
- ✅ 서비스 상태 확인
- ✅ 자동 시작 서비스 등록
- ✅ 방화벽 설정
- ✅ 로그 로테이션 설정

## 📝 수동 배포

### 1. 시스템 준비

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install -y curl wget git

# Docker 설치
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

### 2. 프로젝트 클론

```bash
# 프로젝트 디렉토리로 이동
cd /opt
sudo git clone https://github.com/djgnfj-svg/kkua.git
sudo chown -R $USER:$USER kkua
cd kkua
```

### 3. 환경변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 환경변수 편집
nano .env
```

### 4. 배포 실행

```bash
# 프로덕션 빌드 및 시작
docker compose -f docker-compose.prod.yml up -d --build

# 서비스 상태 확인
docker compose -f docker-compose.prod.yml ps
```

## ⚙️ 환경변수 설정

`.env` 파일에서 다음 변수들을 설정하세요:

### 필수 변수

```bash
# 데이터베이스 설정
POSTGRES_PASSWORD=your-secure-password-here

# 보안 키 (반드시 변경!)
SECRET_KEY=your-super-secret-key-minimum-32-characters
JWT_SECRET=your-jwt-secret-key-minimum-32-characters

# CORS 설정
CORS_ORIGINS=http://your-domain.com,https://your-domain.com
```

### 자동 생성 스크립트

```bash
# 보안 키 자동 생성
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env

# EC2 Public IP 자동 감지
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "CORS_ORIGINS=http://localhost:3000,http://${PUBLIC_IP}" >> .env
```

## ✅ 배포 후 확인

### 서비스 상태 확인

```bash
# 컨테이너 상태
docker compose -f docker-compose.prod.yml ps

# 서비스 로그
docker compose -f docker-compose.prod.yml logs -f

# 개별 서비스 로그
docker compose -f docker-compose.prod.yml logs nginx
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs frontend
```

### 헬스체크

```bash
# 웹 서비스 확인
curl http://localhost/health

# API 서비스 확인
curl http://localhost/api/health

# 각 컨테이너 헬스체크
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### 접속 테스트

| 서비스 | URL | 설명 |
|--------|-----|------|
| **게임** | http://YOUR_IP | 메인 게임 페이지 |
| **API 문서** | http://YOUR_IP/docs | FastAPI Swagger 문서 |
| **헬스체크** | http://YOUR_IP/health | 서비스 상태 확인 |

## 🔧 문제 해결

### 자주 발생하는 문제들

#### 1. 메모리 부족 오류

```bash
# 스왑 메모리 설정 (2GB)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
```

#### 2. Docker 권한 오류

```bash
# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER
newgrp docker

# 또는 로그아웃 후 재로그인
```

#### 3. 포트 충돌

```bash
# 포트 사용 중인 프로세스 확인
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443

# 프로세스 종료
sudo pkill -f nginx
```

#### 4. 데이터베이스 연결 실패

```bash
# PostgreSQL 컨테이너 확인
docker logs kkua-db

# 데이터베이스 접속 테스트
docker exec -it kkua-db psql -U postgres -d kkua_db
```

#### 5. 프론트엔드 빌드 실패

```bash
# 노드 모듈 캐시 정리 후 재빌드
docker compose -f docker-compose.prod.yml build --no-cache frontend
```

### 로그 확인

```bash
# 전체 서비스 로그
docker compose -f docker-compose.prod.yml logs

# 실시간 로그 모니터링
docker compose -f docker-compose.prod.yml logs -f

# 특정 서비스 로그
docker logs kkua-backend
docker logs kkua-frontend
docker logs kkua-nginx
```

## 🛠 관리 명령어

### 서비스 관리

```bash
# 서비스 시작
docker compose -f docker-compose.prod.yml up -d

# 서비스 중지
docker compose -f docker-compose.prod.yml down

# 서비스 재시작
docker compose -f docker-compose.prod.yml restart

# 특정 서비스만 재시작
docker compose -f docker-compose.prod.yml restart backend
```

### 업데이트

```bash
# 코드 업데이트
git pull origin main

# 서비스 중지 후 재빌드
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

### 백업 및 복원

```bash
# 데이터베이스 백업
docker exec kkua-db pg_dump -U postgres kkua_db > backup.sql

# 데이터베이스 복원
docker exec -i kkua-db psql -U postgres kkua_db < backup.sql

# 볼륨 백업
docker run --rm -v kkua_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

### 모니터링

```bash
# 시스템 리소스 사용량
docker stats

# 디스크 사용량
docker system df

# 네트워크 상태
docker network ls
docker network inspect kkua_kkua-network
```

### 정리

```bash
# 사용하지 않는 이미지 정리
docker image prune -f

# 전체 정리 (주의: 모든 정지된 컨테이너, 네트워크, 이미지 삭제)
docker system prune -a
```

## 🔒 보안 설정

### SSL 인증서 설정 (선택사항)

```bash
# Certbot 설치
sudo apt install -y certbot

# SSL 인증서 발급
sudo certbot certonly --standalone -d your-domain.com

# nginx 설정 파일에서 SSL 설정 활성화
sudo nano nginx.prod.conf
```

### 방화벽 설정

```bash
# UFW 활성화
sudo ufw enable

# 필요한 포트만 열기
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# 상태 확인
sudo ufw status
```

## 📊 성능 최적화

### 데이터베이스 최적화

```bash
# PostgreSQL 설정 튜닝
docker exec -it kkua-db psql -U postgres -c "ANALYZE;"
```

### Redis 메모리 최적화

```bash
# Redis 메모리 사용량 확인
docker exec kkua-redis redis-cli INFO memory
```

## 📞 지원

문제가 발생하면:

1. **로그 확인**: `docker compose -f docker-compose.prod.yml logs`
2. **GitHub Issues**: [프로젝트 이슈 페이지](https://github.com/djgnfj-svg/kkua/issues)
3. **서비스 재시작**: `docker compose -f docker-compose.prod.yml restart`

---

**🎮 Happy Gaming! 끝말잇기의 재미를 EC2에서 경험해보세요! 🎉**