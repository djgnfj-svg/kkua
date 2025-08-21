# 🚀 AWS Lightsail 배포 가이드

## 📋 배포 준비 완료!

다음 파일들이 준비되었습니다:
- ✅ `backend/.env.prod` - 백엔드 프로덕션 환경변수
- ✅ `frontend/.env.production` - 프론트엔드 프로덕션 환경변수  
- ✅ `docker-compose.lightsail.yml` - 간소화된 Docker 설정
- ✅ `generate-secrets.sh` - 보안 키 생성 스크립트
- ✅ `nginx/nginx.conf` - Nginx 설정

## 🔧 배포 전 준비사항

### 1. 보안 키 생성
```bash
./generate-secrets.sh
```

### 2. 환경변수 파일 업데이트
- `backend/.env.prod`에서 `your-domain.com`을 실제 도메인으로 변경
- `frontend/.env.production`에서 `your-domain.com`을 실제 도메인으로 변경
- `nginx/nginx.conf`에서 `your-domain.com`을 실제 도메인으로 변경

## 🚀 Lightsail 배포 단계

### 1. Lightsail 인스턴스 생성
- AWS Lightsail 콘솔 접속
- "인스턴스 생성" 클릭
- **OS**: Ubuntu 22.04 LTS
- **플랜**: $5/월 (1GB RAM, 1vCPU, 40GB SSD)
- **키 페어**: 새로 생성 또는 기존 사용

### 2. 서버 접속 및 Docker 설치
```bash
# SSH 접속
ssh -i your-key.pem ubuntu@your-lightsail-ip

# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 설치
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker ubuntu
sudo systemctl enable docker
sudo systemctl start docker

# 재접속 (docker 그룹 적용)
exit
ssh -i your-key.pem ubuntu@your-lightsail-ip
```

### 3. 프로젝트 코드 업로드
```bash
# Git에서 클론하거나 파일 업로드
git clone https://github.com/your-username/kkua.git
cd kkua

# 또는 scp로 파일 업로드
# scp -i your-key.pem -r ./kkua ubuntu@your-lightsail-ip:~/
```

### 4. 환경 설정
```bash
# 보안 키 생성
./generate-secrets.sh

# 환경변수 파일 복사
cp .env.lightsail .env

# 도메인 설정 (실제 도메인으로 변경)
sed -i 's/your-domain.com/your-actual-domain.com/g' backend/.env.prod
sed -i 's/your-domain.com/your-actual-domain.com/g' frontend/.env.production
sed -i 's/your-domain.com/your-actual-domain.com/g' nginx/nginx.conf
```

### 5. SSL 인증서 설정 (Let's Encrypt)
```bash
# Certbot 설치
sudo apt install certbot -y

# SSL 인증서 발급
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# 인증서 디렉토리 생성 및 복사
mkdir -p ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/
sudo chown ubuntu:ubuntu ssl/*
```

### 6. 배포 실행
```bash
# Docker 이미지 빌드 및 실행
docker-compose -f docker-compose.lightsail.yml up -d --build

# 서비스 상태 확인
docker-compose -f docker-compose.lightsail.yml ps
```

### 7. 방화벽 설정
- Lightsail 콘솔에서 네트워킹 탭으로 이동
- 포트 80 (HTTP), 443 (HTTPS) 허용

## 🔍 배포 확인

### 서비스 상태 확인
```bash
# 컨테이너 상태 확인
docker ps

# 로그 확인
docker-compose -f docker-compose.lightsail.yml logs -f

# 헬스체크
curl http://your-domain.com/api/health
```

### 브라우저 테스트
- https://your-domain.com 접속
- 게임 생성 및 플레이 테스트
- WebSocket 연결 확인

## 🛠️ 유지보수 명령어

```bash
# 서비스 재시작
docker-compose -f docker-compose.lightsail.yml restart

# 업데이트 배포
git pull
docker-compose -f docker-compose.lightsail.yml up -d --build

# 로그 확인
docker-compose -f docker-compose.lightsail.yml logs backend
docker-compose -f docker-compose.lightsail.yml logs frontend

# 데이터베이스 백업
docker exec kkua-db pg_dump -U postgres kkua_db > backup_$(date +%Y%m%d).sql
```

## 🆘 문제 해결

### 자주 발생하는 문제들
1. **SSL 인증서 오류**: 도메인 DNS 설정 확인
2. **WebSocket 연결 실패**: nginx 설정의 websocket 프록시 확인  
3. **데이터베이스 연결 오류**: 컨테이너 간 네트워크 연결 확인
4. **메모리 부족**: Lightsail 플랜 업그레이드 고려

### 로그 위치
- Nginx: `docker-compose logs nginx`
- 백엔드: `docker-compose logs backend`
- 데이터베이스: `docker-compose logs db`

## 💰 비용 예상
- **Lightsail 인스턴스**: $5/월
- **도메인**: $10-15/년
- **총 운영비용**: 약 $60-80/년

🎉 **배포 완료!** 이제 여러분의 끄아 게임을 전 세계와 함께 즐기세요!