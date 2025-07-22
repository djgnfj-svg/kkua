# 배포 가이드

## 개발 환경 배포

```bash
# 1. 클론 및 설정
git clone <repository-url>
cd kkua
cp backend/.env.example backend/.env

# 2. 배포 실행
./deploy.sh

# 3. 확인
curl http://localhost:3000  # 프론트엔드
curl http://localhost:8000/health  # 백엔드 헬스체크
```

## 운영 환경 배포

```bash
# 1. 환경 설정
cp backend/.env.example backend/.env
# .env 파일에서 다음 값들을 운영 환경에 맞게 수정:
# - ENVIRONMENT=production
# - DEBUG=false  
# - SECRET_KEY=강력한-비밀키
# - DB_PASSWORD=안전한-비밀번호

# 2. 운영 배포
./deploy.sh production

# 3. 확인
curl http://localhost:8000/health
```

## 주요 명령어

### 서비스 관리
```bash
# 시작
./deploy.sh

# 중지
./stop.sh

# 재시작
docker-compose restart

# 상태 확인
docker-compose ps
```

### 모니터링
```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f backend
docker-compose logs -f frontend

# 리소스 사용량
docker stats
```

### 데이터 관리
```bash
# 데이터베이스 백업
docker exec kkua-db-1 pg_dump -U postgres mydb > backup.sql

# 백업 복원
docker exec -i kkua-db-1 psql -U postgres mydb < backup.sql

# 테스트 실행
docker-compose run --rm backend-test
```

## 문제 해결

### 서비스가 시작되지 않을 때
```bash
# 로그 확인
docker-compose logs

# 포트 충돌 확인
netstat -tulpn | grep :8000
netstat -tulpn | grep :3000

# 완전 재시작
docker-compose down -v
./deploy.sh
```

### 데이터베이스 연결 문제
```bash
# DB 상태 확인
docker-compose exec db pg_isready -U postgres

# DB 재시작
docker-compose restart db
```

### 성능 최적화

**개발 환경**
- 파일 변경 시 자동 재로드 활성화
- 디버그 모드 활성화

**운영 환경** 
- 프론트엔드 프로덕션 빌드 사용
- 워커 프로세스 증가 (uvicorn --workers 4)
- 디버그 모드 비활성화

## 환경별 설정

### 개발 환경 (.env)
```
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=development-key
```

### 운영 환경 (.env)
```
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=강력한-운영-비밀키
DB_PASSWORD=안전한-데이터베이스-비밀번호
```

---

더 자세한 기술 문서는 [CLAUDE.md](./CLAUDE.md)를 참고하세요.