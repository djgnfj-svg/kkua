# 끄아(KKUA) V2 기능 체크리스트 및 테스트 가이드

## 🚀 개발 진행 상황

### Phase 3 완료 (2024년) ✅
**게임 엔진 및 서비스 아키텍처 완성**
- ✅ 완전한 서비스 기반 아키텍처 구현
- ✅ 실시간 게임 엔진 (game_engine.py)
- ✅ 한국어 단어 검증 시스템 (word_validator.py) 
- ✅ 비동기 타이머 서비스 (timer_service.py)
- ✅ 종합 점수 계산 시스템 (score_calculator.py)
- ✅ WebSocket 게임 핸들러 통합 및 최적화

### Phase 4 완료 (2024년) ✅
**아이템 시스템 완성**
- ✅ 종합적인 아이템 서비스 구현 (services/item_service.py)
- ✅ 10가지 아이템 효과 타입 및 핸들러 시스템
- ✅ Redis 기반 쿨다운 및 활성 효과 관리
- ✅ WebSocket 게임 핸들러 완전 통합
- ✅ 성과 기반 랜덤 아이템 드롭 시스템
- ✅ 희귀도별 드롭률 및 밸런싱 시스템

### 향후 계획
- **Phase 5**: 고급 기능 및 최적화
- **Phase 6**: 테스트 및 배포 준비
- **Phase 7**: 모니터링 및 성능 튜닝

---

## 필수 기능 체크리스트

### 🎮 핵심 게임 기능

#### 게임 룸 관리
- [x] 게임 룸 생성 (최대 8명) ✨ **Phase 3 완료**
- [x] 게임 룸 참가/나가기 ✨ **Phase 3 완료**
- [x] 플레이어 목록 실시간 업데이트 ✨ **Phase 3 완료**
- [x] 방장 권한 관리 (게임 시작/설정 변경) ✨ **Phase 3 완료**
- [x] 룸 상태 관리 (대기/진행중/종료) ✨ **Phase 3 완료**

#### 실시간 게임 플레이
- [x] 턴 기반 게임 진행 ✨ **Phase 3 완료**
- [x] 30초 턴 타이머 (실시간 카운트다운) ✨ **Phase 3 완료**
- [x] 단어 입력 및 제출 ✨ **Phase 3 완료**
- [x] 끝말잇기 규칙 검증 (마지막 글자 = 첫 글자) ✨ **Phase 3 완료**
- [x] 한국어 단어 유효성 검증 ✨ **Phase 3 완료**
- [x] 중복 단어 사용 방지 ✨ **Phase 3 완료**
- [x] 자동 턴 넘김 (시간 만료 시) ✨ **Phase 3 완료**

#### 점수 시스템
- [x] 기본 점수: 글자 수 × 난이도 배수 ✨ **Phase 3 완료**
- [x] 속도 보너스: 빠른 응답 시 추가 점수 ✨ **Phase 3 완료**
- [x] 콤보 시스템: 연속 성공 시 점수 배수 ✨ **Phase 3 완료**
- [x] 단어 희귀도별 보너스 점수 ✨ **Phase 3 완료**
- [x] 실시간 점수 업데이트 및 표시 ✨ **Phase 3 완료**

#### 아이템 시스템
- [x] 5가지 희귀도 아이템 (common/uncommon/rare/epic/legendary) ✨ **Phase 4 완료**
- [x] 아이템 효과 구현: ✨ **Phase 4 완료**
  - [x] **시간 연장**: 턴 시간 10초 추가 ✨ **Phase 4 완료**
  - [x] **점수 배수**: 다음 단어 점수 2배 ✨ **Phase 4 완료**
  - [x] **글자 힌트**: 다음 가능한 글자 3개 표시 ✨ **Phase 4 완료**
  - [x] **상대 방해**: 상대방 시간 5초 단축 ✨ **Phase 4 완료**
  - [x] **보호막**: 한 턴 동안 아이템 공격 무효 ✨ **Phase 4 완료**
  - [x] **추가 효과**: 동결, 추가턴, 단어훔치기, 콤보부스트, 부활 ✨ **Phase 4 완료**
- [x] 아이템 인벤토리 관리 ✨ **Phase 4 완료**
- [x] 아이템 사용 쿨다운 시스템 ✨ **Phase 4 완료**
- [x] 게임 종료 시 랜덤 아이템 지급 ✨ **Phase 4 완료**

### 📊 데이터 및 리포트

#### 단어 정보 시스템
- [x] 단어 정의 표시 ✨ **Phase 3 완료**
- [x] 단어 난이도 레벨 (1~3) ✨ **Phase 3 완료**
- [x] 단어 사용 빈도 점수 ✨ **Phase 3 완료**
- [x] 단어 타입 분류 (명사/동사/형용사 등) ✨ **Phase 3 완료**
- [x] 실시간 단어 정보 표시 ✨ **Phase 3 완료**

#### 게임 리포트
- [ ] 게임 종료 후 상세 리포트 생성
- [ ] 개별 플레이어 통계:
  - [ ] 총 점수 및 순위
  - [ ] 제출한 단어 목록
  - [ ] 평균 응답 시간
  - [ ] 사용한 아이템 목록
  - [ ] 최대 콤보 기록
  - [ ] 정확도 비율
- [ ] 게임 하이라이트:
  - [ ] 가장 긴 단어
  - [ ] 가장 빠른 응답
  - [ ] 가장 높은 점수 단어
  - [ ] 최대 콤보 달성

#### 로깅 시스템
- [ ] 모든 게임 이벤트 실시간 로깅
- [ ] 게임 시작/종료 기록
- [ ] 단어 제출 및 검증 기록
- [ ] 아이템 사용 기록
- [ ] 플레이어 참가/이탈 기록
- [ ] 에러 및 예외 상황 로깅
- [ ] 성능 메트릭 수집

### 🔧 기술적 기능

#### WebSocket 통신
- [x] 실시간 양방향 통신 ✨ **Phase 3 완료**
- [x] 자동 재연결 (exponential backoff) ✨ **기존 구현**
- [x] 메시지 큐 관리 ✨ **Phase 3 완료**
- [x] 연결 상태 추적 및 표시 ✨ **기존 구현**
- [x] JWT 토큰 기반 인증 ✨ **기존 구현**

#### 상태 관리
- [x] Redis 기반 실시간 상태 관리 ✨ **Phase 3 완료**
- [x] PostgreSQL 기반 영구 데이터 저장 ✨ **기존 구현**
- [x] 클라이언트-서버 상태 동기화 ✨ **Phase 3 완료**
- [x] 낙관적 업데이트 및 서버 검증 ✨ **Phase 3 완료**

#### 성능 및 확장성
- [ ] 1000명 동시 접속 지원
- [ ] 100개 동시 게임룸 지원
- [ ] 메모리 누수 방지
- [ ] 데이터베이스 쿼리 최적화
- [ ] Redis 캐싱 활용

## 테스트 시나리오

### 🧪 기본 게임 플로우 테스트

#### 시나리오 1: 정상적인 2인 게임
```
1. 플레이어 A가 게임룸 생성
2. 플레이어 B가 게임룸 참가
3. 플레이어 A가 게임 시작
4. 턴 순서대로 단어 제출 (5라운드)
5. 게임 종료 및 결과 확인
6. 게임 리포트 생성 확인
```

#### 시나리오 2: 아이템 사용 게임
```
1. 4명 플레이어로 게임 시작
2. 각 플레이어가 서로 다른 아이템 사용
3. 아이템 효과 정상 작동 확인
4. 아이템 쿨다운 시간 확인
5. 게임 종료 후 아이템 사용 로그 확인
```

#### 시나리오 3: 에러 상황 처리
```
1. 잘못된 단어 제출 (끝말잇기 규칙 위반)
2. 중복 단어 제출
3. 존재하지 않는 단어 제출
4. 타이머 만료 상황
5. 네트워크 연결 끊김 및 재연결
```

### 🚀 성능 테스트

#### 부하 테스트 1: 동시 접속
```python
async def test_concurrent_connections():
    """1000명 동시 WebSocket 연결 테스트"""
    connections = []
    
    # 1000개 동시 연결 생성
    for i in range(1000):
        conn = await create_websocket_connection(f"user_{i}")
        connections.append(conn)
    
    # 모든 연결이 정상인지 확인
    assert len(connections) == 1000
    
    # 연결 정리
    await disconnect_all(connections)
```

#### 부하 테스트 2: 동시 게임
```python
async def test_concurrent_games():
    """100개 게임룸에서 동시 게임 테스트"""
    tasks = []
    
    # 100개 게임룸 생성
    for i in range(100):
        task = simulate_full_game(
            room_id=f"room_{i}",
            players=4,
            rounds=10
        )
        tasks.append(task)
    
    # 모든 게임 정상 완료 확인
    results = await asyncio.gather(*tasks)
    assert all(result.completed for result in results)
```

#### 메모리 누수 테스트
```python
def test_memory_leak():
    """장시간 실행 시 메모리 누수 테스트"""
    initial_memory = get_memory_usage()
    
    # 1시간 동안 게임 반복 실행
    for _ in range(1000):
        simulate_quick_game()
        
    final_memory = get_memory_usage()
    memory_increase = final_memory - initial_memory
    
    # 메모리 증가가 임계값 이하인지 확인
    assert memory_increase < MAX_MEMORY_INCREASE
```

### 🔒 보안 테스트

#### 인증 테스트
```python
def test_websocket_authentication():
    """WebSocket 인증 테스트"""
    # 유효한 토큰으로 연결
    valid_conn = connect_with_token(valid_jwt_token)
    assert valid_conn.is_authenticated
    
    # 무효한 토큰으로 연결 시도
    with pytest.raises(AuthenticationError):
        connect_with_token(invalid_jwt_token)
    
    # 토큰 없이 연결 시도
    with pytest.raises(AuthenticationError):
        connect_without_token()
```

#### 입력 검증 테스트
```python
def test_input_validation():
    """사용자 입력 검증 테스트"""
    # SQL 인젝션 시도
    malicious_word = "'; DROP TABLE users; --"
    response = submit_word(malicious_word)
    assert response.error == "INVALID_WORD"
    
    # XSS 시도
    xss_word = "<script>alert('xss')</script>"
    response = submit_word(xss_word)
    assert response.error == "INVALID_WORD"
    
    # 너무 긴 단어
    long_word = "a" * 1000
    response = submit_word(long_word)
    assert response.error == "WORD_TOO_LONG"
```

## 성능 벤치마크

### 응답 시간 목표
- **WebSocket 메시지 처리**: < 10ms
- **단어 검증**: < 50ms  
- **데이터베이스 쿼리**: < 100ms
- **게임 상태 업데이트**: < 20ms
- **리포트 생성**: < 500ms

### 처리량 목표
- **동시 WebSocket 연결**: 1,000개 이상
- **초당 메시지 처리**: 10,000개 이상
- **동시 활성 게임**: 100개 이상
- **일일 게임 수**: 10,000게임 이상

### 리소스 사용량 목표
- **서버 메모리**: < 2GB
- **Redis 메모리**: < 1GB  
- **CPU 사용률**: < 70%
- **데이터베이스 연결**: < 100개

## 배포 전 검증 체크리스트

### 🏗️ 인프라 준비
- [ ] Docker 컨테이너 빌드 성공
- [ ] Docker Compose 설정 검증
- [ ] 환경 변수 설정 완료
- [ ] 데이터베이스 마이그레이션 성공
- [ ] Redis 연결 확인
- [ ] SSL 인증서 설정 (프로덕션)

### 📋 기능 검증
- [ ] 모든 API 엔드포인트 테스트 통과
- [ ] WebSocket 연결 및 메시지 전송 테스트
- [ ] 게임 전체 플로우 테스트 (시작~종료)
- [ ] 아이템 시스템 전체 테스트
- [ ] 에러 상황 처리 테스트
- [ ] 동시성 테스트 통과

### 🛡️ 보안 검증
- [ ] 인증/권한 시스템 테스트
- [ ] 입력 검증 및 sanitization 확인
- [ ] SQL 인젝션 방어 테스트
- [ ] XSS 방어 테스트  
- [ ] rate limiting 동작 확인
- [ ] 로그에 민감정보 노출 여부 확인

### ⚡ 성능 검증
- [ ] 부하 테스트 (1000 동시 사용자)
- [ ] 메모리 누수 테스트 (24시간 실행)
- [ ] 응답 시간 벤치마크 달성
- [ ] 데이터베이스 성능 최적화 확인
- [ ] Redis 캐시 적중률 확인

### 📊 모니터링 설정
- [ ] 로그 수집 시스템 동작
- [ ] 메트릭 수집 및 대시보드 설정
- [ ] 알람 규칙 설정 및 테스트
- [ ] 헬스 체크 엔드포인트 구현
- [ ] 백업 및 복구 절차 준비

## 사용자 시나리오 테스트

### 시나리오 A: 신규 사용자
```
1. 첫 접속 시 닉네임 설정
2. 튜토리얼/도움말 확인
3. 첫 게임 참여 (AI와 연습게임)
4. 실제 플레이어와 게임
5. 아이템 획득 및 사용법 학습
```

### 시나리오 B: 숙련 사용자
```
1. 빠른 게임 매칭
2. 다양한 아이템 조합 사용
3. 고득점 달성 시도
4. 친구와 비공개 게임
5. 게임 통계 및 기록 확인
```

### 시나리오 C: 그룹 플레이
```
1. 4명이 함께 게임룸 생성
2. 게임 설정 커스터마이징
3. 여러 라운드 연속 진행
4. 팀전 모드 (향후 기능)
5. 그룹 통계 및 랭킹 확인
```

이 체크리스트를 통해 끄아(KKUA) V2의 모든 기능이 정상 작동하는지 체계적으로 검증할 수 있습니다. 각 항목을 순서대로 테스트하여 완성도 높은 게임을 출시하세요.