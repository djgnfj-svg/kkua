# 🚀 끄아(KKUA) V2 - AWS Lightsail 배포 가이드

## 📋 목차
1. [사전 준비](#사전-준비)
2. [AWS Lightsail 설정](#aws-lightsail-설정)
3. [서버 환경 구축](#서버-환경-구축)
4. [프로젝트 배포](#프로젝트-배포)
5. [도메인 및 SSL 설정](#도메인-및-ssl-설정)
6. [배포 완료 확인](#배포-완료-확인)
7. [문제 해결](#문제-해결)

---

## 🛠️ 사전 준비

### 필요한 것들
- [ ] AWS 계정
- [ ] 도메인 (선택사항, IP로도 접속 가능)
- [ ] SSH 클라이언트 (Windows: PuTTY, Mac/Linux: 터미널)

### 예상 비용
- **AWS Lightsail**: $5/월 (1GB RAM, 1vCPU, 40GB SSD)
- **도메인**: $10-15/년 (선택사항)
- **총 예상 비용**: 월 $5 (연간 $60 + 도메인비)

---

## ☁️ AWS Lightsail 설정

### 1단계: Lightsail 인스턴스 생성

1. **AWS 콘솔 접속**
   - https://lightsail.aws.amazon.com/ 접속
   - AWS 계정으로 로그인

2. **인스턴스 생성**
   - "인스턴스 생성" 버튼 클릭
   - **인스턴스 위치**: 가장 가까운 지역 선택 (예: ap-northeast-2, Seoul)

3. **운영체제 선택**
   - "Linux/Unix" 선택
   - **플랫폼**: Ubuntu
   - **블루프린트**: Ubuntu 22.04 LTS

4. **인스턴스 플랜 선택**
   - **$5/월 플랜** 선택 (1GB RAM, 1vCPU, 40GB SSD)
   - 처음에는 이것만으로도 충분함

5. **인스턴스 식별**
   - **인스턴스 이름**: `kkua-game-server`
   - "인스턴스 생성" 클릭

6. **키 페어 다운로드**
   - 생성 완료 후 SSH 키 다운로드
   - 안전한 곳에 보관 (예: `kkua-lightsail-key.pem`)

---

## 🖥️ 서버 환경 구축

### 2단계: 서버 접속 및 기본 설정

1. **SSH 접속** (Windows)
   ```bash
   # PuTTY 사용 또는 Windows Terminal에서:
   ssh -i kkua-lightsail-key.pem ubuntu@YOUR_LIGHTSAIL_IP
   ```

2. **SSH 접속** (Mac/Linux)
   ```bash
   chmod 400 kkua-lightsail-key.pem
   ssh -i kkua-lightsail-key.pem ubuntu@YOUR_LIGHTSAIL_IP
   ```

3. **시스템 업데이트**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

### 3단계: Docker 설치

```bash
# Docker 설치
sudo apt install docker.io docker-compose -y

# Docker 권한 설정
sudo usermod -aG docker ubuntu

# Docker 서비스 시작
sudo systemctl enable docker
sudo systemctl start docker

# 재접속 (권한 적용을 위해)
exit
ssh -i kkua-lightsail-key.pem ubuntu@YOUR_LIGHTSAIL_IP

# Docker 설치 확인
docker --version
docker-compose --version
```

---

## 📦 프로젝트 배포

### 4단계: 프로젝트 코드 업로드

**방법 1: Git Clone (추천)**
```bash
# Git 설치
sudo apt install git -y

# 프로젝트 클론
git clone https://github.com/djgnfj-svg/kkua.git
cd kkua
```

**방법 2: 파일 업로드**
```bash
# 로컬에서 서버로 파일 업로드
scp -i kkua-lightsail-key.pem -r ./kkua ubuntu@YOUR_LIGHTSAIL_IP:~/
```

### 5단계: 환경 설정

1. **보안 키 생성**
   ```bash
   cd ~/kkua
   ./generate-secrets.sh
   ```

2. **도메인 설정** (도메인이 있는 경우)
   ```bash
   # 실제 도메인으로 변경
   sed -i 's/your-domain.com/실제도메인.com/g' backend/.env.prod
   sed -i 's/your-domain.com/실제도메인.com/g' frontend/.env.production
   sed -i 's/your-domain.com/실제도메인.com/g' nginx/nginx.conf
   ```

3. **환경변수 파일 복사**
   ```bash
   cp .env.lightsail .env
   ```

---

## 🌐 도메인 및 SSL 설정

### 6단계: DNS 설정 (도메인이 있는 경우)

1. **도메인 제공업체에서 A 레코드 설정**
   - `@` (또는 도메인명) → `YOUR_LIGHTSAIL_IP`
   - `www` → `YOUR_LIGHTSAIL_IP`

2. **DNS 전파 확인** (5-10분 소요)
   ```bash
   nslookup 실제도메인.com
   ```

### 7단계: SSL 인증서 설정

1. **Certbot 설치**
   ```bash
   sudo apt install certbot -y
   ```

2. **SSL 인증서 발급**
   ```bash
   # 도메인이 있는 경우
   sudo certbot certonly --standalone -d 실제도메인.com -d www.실제도메인.com
   
   # IP만 사용하는 경우 (SSL 스킵)
   mkdir -p ssl
   # 이 경우 nginx.conf에서 SSL 설정 제거 필요
   ```

3. **인증서 복사** (도메인이 있는 경우)
   ```bash
   mkdir -p ssl
   sudo cp /etc/letsencrypt/live/실제도메인.com/fullchain.pem ssl/
   sudo cp /etc/letsencrypt/live/실제도메인.com/privkey.pem ssl/
   sudo chown ubuntu:ubuntu ssl/*
   ```

---

## 🚀 프로젝트 배포

### 8단계: Docker 배포 실행

1. **데이터베이스 비밀번호 설정**
   ```bash
   # .env 파일에서 DB_PASSWORD 확인
   cat .env
   ```

2. **Docker 이미지 빌드 및 실행**
   ```bash
   # 빌드 및 실행
   docker-compose -f docker-compose.lightsail.yml up -d --build
   
   # 빌드 진행 상황 확인
   docker-compose -f docker-compose.lightsail.yml logs -f
   ```

3. **서비스 상태 확인**
   ```bash
   # 컨테이너 상태 확인
   docker-compose -f docker-compose.lightsail.yml ps
   
   # 각 서비스 로그 확인
   docker-compose -f docker-compose.lightsail.yml logs backend
   docker-compose -f docker-compose.lightsail.yml logs frontend
   docker-compose -f docker-compose.lightsail.yml logs nginx
   ```

### 9단계: 방화벽 설정

1. **Lightsail 네트워킹 설정**
   - Lightsail 콘솔 → 인스턴스 → "네트워킹" 탭
   - 다음 포트들 열기:
     - **HTTP**: 포트 80
     - **HTTPS**: 포트 443 (SSL 사용 시)
     - **SSH**: 포트 22 (기본으로 열려있음)

---

## ✅ 배포 완료 확인

### 10단계: 서비스 테스트

1. **헬스체크 확인**
   ```bash
   # 백엔드 헬스체크
   curl http://localhost:8000/health
   
   # 또는 외부에서
   curl http://YOUR_LIGHTSAIL_IP/api/health
   ```

2. **웹사이트 접속 테스트**
   - **도메인이 있는 경우**: https://실제도메인.com
   - **IP만 사용하는 경우**: http://YOUR_LIGHTSAIL_IP

3. **게임 기능 테스트**
   - 게임 방 생성
   - 플레이어 입장
   - 끝말잇기 플레이
   - 실시간 채팅
   - 시각적 효과 확인

---

## 🔧 유지보수 명령어

### 일상적인 관리

```bash
# 서비스 재시작
docker-compose -f docker-compose.lightsail.yml restart

# 서비스 중지
docker-compose -f docker-compose.lightsail.yml down

# 서비스 시작
docker-compose -f docker-compose.lightsail.yml up -d

# 로그 실시간 확인
docker-compose -f docker-compose.lightsail.yml logs -f

# 특정 서비스 로그만 확인
docker-compose -f docker-compose.lightsail.yml logs backend
docker-compose -f docker-compose.lightsail.yml logs frontend
docker-compose -f docker-compose.lightsail.yml logs nginx
```

### 업데이트 배포

```bash
# 1. 최신 코드 가져오기
git pull origin develop

# 2. 재빌드 및 배포
docker-compose -f docker-compose.lightsail.yml up -d --build

# 3. 이전 이미지 정리
docker system prune -f
```

### 데이터베이스 백업

```bash
# 백업 생성
docker exec kkua-db pg_dump -U postgres kkua_db > backup_$(date +%Y%m%d).sql

# 백업 복원 (필요시)
docker exec -i kkua-db psql -U postgres kkua_db < backup_20240820.sql
```

---

## 🆘 문제 해결

### 자주 발생하는 문제들

#### 1. "컨테이너가 시작되지 않아요"
```bash
# 로그 확인
docker-compose -f docker-compose.lightsail.yml logs

# 개별 컨테이너 상태 확인
docker ps -a

# 컨테이너 재시작
docker-compose -f docker-compose.lightsail.yml restart
```

#### 2. "웹사이트에 접속이 안 돼요"
```bash
# nginx 설정 확인
docker-compose -f docker-compose.lightsail.yml logs nginx

# 포트 확인
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443

# 방화벽 확인
sudo ufw status
```

#### 3. "게임이 연결되지 않아요"
```bash
# 백엔드 서비스 확인
curl http://localhost:8000/health

# WebSocket 연결 확인
docker-compose -f docker-compose.lightsail.yml logs backend | grep -i websocket

# Redis 연결 확인
docker exec kkua-redis redis-cli ping
```

#### 4. "SSL 인증서 오류"
```bash
# 인증서 상태 확인
sudo certbot certificates

# 인증서 갱신
sudo certbot renew

# nginx 재시작
docker-compose -f docker-compose.lightsail.yml restart nginx
```

### 로그 위치 및 디버깅

```bash
# 전체 서비스 로그
docker-compose -f docker-compose.lightsail.yml logs

# 실시간 로그 모니터링
docker-compose -f docker-compose.lightsail.yml logs -f backend

# 에러만 필터링
docker-compose -f docker-compose.lightsail.yml logs | grep -i error

# 최근 로그만 확인
docker-compose -f docker-compose.lightsail.yml logs --tail=50
```

---

## 📊 성능 모니터링

### 서버 리소스 확인
```bash
# CPU 및 메모리 사용량
htop

# 디스크 사용량
df -h

# Docker 컨테이너 리소스 사용량
docker stats
```

### 게임 성능 확인
```bash
# 동시 접속자 수 (Redis에서 확인)
docker exec kkua-redis redis-cli info clients

# 활성 게임 방 수
docker exec kkua-redis redis-cli keys "room:*" | wc -l
```

---

## 🔒 보안 체크리스트

- [ ] SSH 키 기반 인증 사용
- [ ] 기본 비밀번호들 모두 변경
- [ ] 방화벽에서 필요한 포트만 허용
- [ ] SSL 인증서 정상 작동
- [ ] 정기적인 백업 실행
- [ ] 시스템 업데이트 정기 실행

---

## 🔄 자동화 스크립트

### SSL 인증서 자동 갱신 설정
```bash
# crontab 편집
sudo crontab -e

# 다음 줄 추가 (매월 1일 새벽 2시에 갱신)
0 2 1 * * certbot renew --quiet && docker-compose -f /home/ubuntu/kkua/docker-compose.lightsail.yml restart nginx
```

### 자동 백업 설정
```bash
# 백업 스크립트 생성
cat > /home/ubuntu/backup.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/kkua
docker exec kkua-db pg_dump -U postgres kkua_db > /home/ubuntu/backups/backup_$(date +%Y%m%d_%H%M%S).sql
find /home/ubuntu/backups -name "backup_*.sql" -mtime +7 -delete
EOF

chmod +x /home/ubuntu/backup.sh

# 백업 디렉토리 생성
mkdir -p /home/ubuntu/backups

# crontab에 추가 (매일 새벽 3시에 백업)
echo "0 3 * * * /home/ubuntu/backup.sh" | sudo crontab -
```

---

## 🎯 배포 완료 후 확인사항

### 기능 테스트 체크리스트
- [ ] 웹사이트 정상 접속
- [ ] 게임 방 생성 가능
- [ ] 플레이어 입장/퇴장 동작
- [ ] 끝말잇기 게임 플레이
- [ ] 실시간 채팅 기능
- [ ] 시각적 효과 작동 (콤보, 타이머 등)
- [ ] 모바일에서도 정상 작동

### 성능 확인
- [ ] 페이지 로딩 속도 < 3초
- [ ] WebSocket 연결 지연 < 100ms
- [ ] 동시 접속 10명 이상 가능

---

## 📞 지원 및 문의

### 유용한 명령어 모음
```bash
# 서비스 상태 한 번에 확인
docker-compose -f docker-compose.lightsail.yml ps && echo "--- 헬스체크 ---" && curl -s http://localhost:8000/health

# 전체 재시작
docker-compose -f docker-compose.lightsail.yml down && docker-compose -f docker-compose.lightsail.yml up -d

# 디스크 정리
docker system prune -f && docker volume prune -f

# 메모리 사용량 확인
free -h && docker stats --no-stream
```

---

## 🎉 축하합니다!

끄아(KKUA) V2가 성공적으로 배포되었습니다! 

🎮 **게임 URL**: https://실제도메인.com (또는 http://YOUR_LIGHTSAIL_IP)

친구들과 함께 실시간 한국어 끝말잇기를 즐겨보세요!

---

## 📈 다음 단계 (선택사항)

1. **사용자 증가 시**: Lightsail 플랜 업그레이드 ($10/월, $20/월)
2. **고가용성 필요 시**: AWS EC2 + RDS로 마이그레이션
3. **글로벌 서비스**: CloudFront CDN 추가
4. **모바일 앱**: React Native로 모바일 앱 개발

---

> 💡 **팁**: 배포 후 첫 24시간 동안은 로그를 자주 확인하여 문제가 없는지 모니터링하세요!