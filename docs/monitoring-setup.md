# 🔍 모니터링 설정 가이드

## Sentry 에러 추적 설정

### 1. Sentry 프로젝트 생성

1. [Sentry.io](https://sentry.io)에서 계정 생성
2. 새 프로젝트 생성 (플랫폼: Python/FastAPI)
3. DSN 복사

### 2. 환경변수 설정

**.env 파일에 추가:**
```bash
# Monitoring & Error Tracking (Sentry)
SENTRY_DSN=https://your-sentry-dsn-here@o123456.ingest.sentry.io/123456
SENTRY_ENVIRONMENT=development  # development, staging, production
SENTRY_TRACES_SAMPLE_RATE=1.0   # 0.0 to 1.0 (1.0 = 100% of transactions)
SENTRY_PROFILES_SAMPLE_RATE=1.0 # 0.0 to 1.0 (1.0 = 100% of transactions)
```

### 3. Docker 환경에서 설정

**docker-compose.yml의 backend 서비스에 환경변수 추가:**
```yaml
backend:
  environment:
    - SENTRY_DSN=${SENTRY_DSN}
    - SENTRY_ENVIRONMENT=development
    - SENTRY_TRACES_SAMPLE_RATE=1.0
    - SENTRY_PROFILES_SAMPLE_RATE=1.0
```

**docker-compose.prod.yml에서는:**
```yaml
backend:
  environment:
    - SENTRY_DSN=${SENTRY_DSN}
    - SENTRY_ENVIRONMENT=production
    - SENTRY_TRACES_SAMPLE_RATE=0.1  # 프로덕션에서는 10%만 샘플링
    - SENTRY_PROFILES_SAMPLE_RATE=0.1
```

## 모니터링 기능

### 자동 에러 추적
- **모든 에러 자동 캡처**: FastAPI 예외, Redis 연결 에러, WebSocket 에러
- **스택트레이스**: 상세한 에러 위치 정보
- **브레드크럼**: 에러 발생 전 이벤트 추적

### 성능 모니터링
- **트랜잭션 추적**: API 엔드포인트별 응답시간
- **데이터베이스 쿼리**: 느린 쿼리 식별
- **Redis 작업**: Redis 연산 성능 추적

### 게임 이벤트 추적
- **게임 생성**: 새 게임 시작 이벤트
- **WebSocket 연결**: 실시간 연결 상태
- **에러 컨텍스트**: 게임 상태와 함께 에러 정보

## 헬스체크 엔드포인트

### 기본 헬스체크
```bash
GET /health
```
응답:
```json
{
  "status": "healthy",
  "environment": "development"
}
```

### 상세 헬스체크
```bash
GET /health/detailed
```
응답:
```json
{
  "status": "healthy",
  "environment": "development",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "services": {
    "redis": {
      "status": "healthy",
      "connected": true
    },
    "postgresql": {
      "status": "healthy", 
      "connected": true
    },
    "sentry": {
      "status": "healthy",
      "configured": true
    }
  }
}
```

## 알림 설정

### Sentry 알림 규칙
1. **Error Alerts**: 새로운 에러 발생 시
2. **Performance Alerts**: 응답시간 임계값 초과 시
3. **Custom Alerts**: 게임 관련 중요 이벤트

### 권장 알림 임계값
- **에러율**: 5% 이상
- **응답시간**: 2초 이상
- **Redis 연결 실패**: 즉시 알림
- **데이터베이스 연결 실패**: 즉시 알림

## 대시보드 설정

### Sentry 대시보드
- **에러 트렌드**: 시간별 에러 발생률
- **성능 개요**: 응답시간 분포
- **릴리스 추적**: 배포별 안정성

### 모니터링 모범 사례
1. **환경별 분리**: development, staging, production
2. **샘플링 설정**: 프로덕션에서는 적절한 샘플링 비율 사용
3. **민감정보 제외**: PII(개인정보) 전송 비활성화
4. **정기적 검토**: 주간 모니터링 리포트 확인

## 트러블슈팅

### 일반적인 문제들

**1. Sentry DSN 설정 오류**
- 증상: "Sentry DSN이 설정되지 않았습니다" 로그
- 해결: `.env` 파일에 올바른 DSN 설정

**2. 높은 에러율**
- 증상: Sentry에서 과도한 에러 알림
- 해결: 샘플링 비율 조정 또는 특정 에러 무시 설정

**3. 성능 이슈**
- 증상: 느린 API 응답
- 해결: Sentry Performance 탭에서 병목 지점 확인

### 로그 위치
- **애플리케이션 로그**: `logs/kkua.log`
- **에러 로그**: `logs/error.log` 
- **성능 로그**: `logs/performance.log`

## 환경별 설정 권장사항

### Development
```bash
SENTRY_TRACES_SAMPLE_RATE=1.0  # 모든 트랜잭션 추적
SENTRY_PROFILES_SAMPLE_RATE=1.0
```

### Production
```bash
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% 샘플링으로 성능 최적화
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

이 설정으로 프로덕션 환경에서 효과적인 모니터링과 에러 추적이 가능합니다.