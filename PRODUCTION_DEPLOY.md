# 🚀 KKUA 프로덕션 배포 가이드

## 📋 배포 전 필수 수정 사항

### 1. `.env.prod` 파일 수정
```bash
# 필수 변경 항목:
POSTGRES_PASSWORD=실제_보안_비밀번호      # ⚠️ 변경 필수!
SECRET_KEY=실제_시크릿_키                 # ⚠️ 변경 필수!
JWT_SECRET=실제_JWT_시크릿_키             # ⚠️ 변경 필수!

# 도메인 설정 (EC2 또는 실제 도메인):
CORS_ORIGINS=http://13.125.132.65        # EC2 IP 또는 도메인
VITE_API_URL=http://13.125.132.65        # EC2 IP 또는 도메인
VITE_WS_URL=ws://13.125.132.65/ws        # WebSocket URL
```

## 🎯 원클릭 배포

### EC2/서버에서:
```bash
# 1. 클론
git clone https://github.com/djgnfj-svg/kkua.git
cd kkua

# 2. .env.prod 수정 (위 필수 항목)
nano .env.prod

# 3. 실행
./prod.sh
```

### 로컬 테스트:
```bash
./prod.sh
```

## 📍 접속 주소
- **웹사이트**: http://서버IP:80
- **API 문서**: http://서버IP:80/api/docs
- **WebSocket**: ws://서버IP:80/ws

## 🔧 관리 명령어
```bash
# 로그 확인
docker-compose --env-file .env.prod logs -f

# 서비스 중지
docker-compose --env-file .env.prod down

# 재시작
docker-compose --env-file .env.prod restart
```

## ⚠️ 주의사항
1. **보안 키는 반드시 변경** - 기본값 사용 금지
2. **CORS 설정** - 실제 도메인/IP로 변경
3. **첫 실행 시** - 데이터 로딩 2-3분 소요

## 🏗️ 아키텍처
```
[nginx:80] → [frontend:80] (정적 파일)
           → [backend:8000] (API/WS)
           → [postgres:5432] + [redis:6379]
```

프로덕션은 frontend를 빌드해서 nginx로 서빙 (Vite dev server X)