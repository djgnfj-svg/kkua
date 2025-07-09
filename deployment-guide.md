# 끄아 (KKUA) 배포 가이드

## 개발 환경 실행

### 1. 사전 준비
```bash
# 저장소 클론
git clone <repository-url>
cd kkua

# 환경 변수 설정
cp backend/.env.example backend/.env
# 필요에 따라 .env 파일 수정
```

### 2. 개발 환경 실행
```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 확인
curl http://localhost:8000/health  # 백엔드 헬스체크
curl http://localhost:3000/        # 프론트엔드 확인
```

### 3. 개발 중 유용한 명령어
```bash
# 백엔드 테스트 실행
docker exec kkua-backend-1 python -m pytest tests/ -v

# 코드 포맷팅
docker exec kkua-backend-1 ruff check . --fix
docker exec kkua-frontend-1 npx prettier --write src/**/*.js

# 특정 서비스 재시작
docker-compose restart backend
docker-compose restart frontend
```

## 프로덕션 배포

### 1. 프로덕션 환경 설정
```bash
# 프로덕션 설정 파일 생성
cp docker-compose.prod.yml docker-compose.yml

# 환경 변수 수정 (프로덕션 설정)
# - DATABASE_URL: 프로덕션 데이터베이스 URL
# - CORS_ORIGINS: 허용할 도메인 목록
# - DEBUG: false로 설정
```

### 2. 프로덕션 빌드 및 실행
```bash
# 프로덕션 환경으로 빌드 및 실행
docker-compose -f docker-compose.prod.yml up -d

# 서비스 상태 확인
docker-compose -f docker-compose.prod.yml ps
```

### 3. 프로덕션 모니터링
```bash
# 로그 모니터링
docker-compose -f docker-compose.prod.yml logs -f

# 헬스체크
curl https://your-domain.com/health
```

## 배포 체크리스트

### 보안 설정
- [ ] 환경 변수에서 비밀번호 및 토큰 확인
- [ ] CORS 설정에서 허용된 도메인만 설정
- [ ] 디버그 모드 비활성화
- [ ] HTTPS 설정 (프로덕션 환경)

### 성능 최적화
- [ ] 프론트엔드 프로덕션 빌드 사용
- [ ] Nginx 압축 설정 활성화
- [ ] 데이터베이스 연결 풀 설정
- [ ] 정적 파일 캐싱 설정

### 모니터링
- [ ] 로그 수집 시스템 설정
- [ ] 헬스체크 엔드포인트 설정
- [ ] 메트릭 수집 설정 (선택사항)

## 문제 해결

### 일반적인 문제들

1. **백엔드 연결 실패**
   ```bash
   # 컨테이너 로그 확인
   docker-compose logs backend
   
   # 데이터베이스 연결 확인
   docker exec -it kkua-db-1 psql -U postgres -d mydb
   ```

2. **프론트엔드 빌드 실패**
   ```bash
   # 의존성 재설치
   docker-compose exec frontend npm install
   
   # 빌드 로그 확인
   docker-compose logs frontend
   ```

3. **데이터베이스 연결 문제**
   ```bash
   # 데이터베이스 컨테이너 상태 확인
   docker-compose ps db
   
   # 헬스체크 상태 확인
   docker-compose exec db pg_isready -U postgres
   ```

### 성능 문제 해결

1. **WebSocket 연결 문제**
   - 프록시 설정에서 WebSocket 업그레이드 지원 확인
   - 방화벽에서 WebSocket 포트 허용 확인

2. **데이터베이스 성능**
   - 연결 풀 설정 최적화
   - 인덱스 확인 및 쿼리 최적화

## 백업 및 복구

### 데이터베이스 백업
```bash
# 데이터베이스 백업
docker exec kkua-db-1 pg_dump -U postgres mydb > backup.sql

# 백업 복구
docker exec -i kkua-db-1 psql -U postgres mydb < backup.sql
```

### 전체 시스템 백업
```bash
# 코드 및 설정 백업
git archive --format=tar.gz --output=kkua-backup.tar.gz HEAD

# 데이터 볼륨 백업
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data.tar.gz /data
```

## 업데이트 절차

### 1. 코드 업데이트
```bash
# 최신 코드 가져오기
git pull origin main

# 서비스 재시작
docker-compose down
docker-compose up -d
```

### 2. 데이터베이스 마이그레이션
```bash
# 마이그레이션 실행 (필요한 경우)
docker exec kkua-backend-1 alembic upgrade head
```

### 3. 무중단 업데이트 (고급)
```bash
# 새 버전 빌드
docker-compose build

# 롤링 업데이트
docker-compose up -d --no-deps --scale backend=2 backend
docker-compose up -d --no-deps --scale backend=1 backend
```