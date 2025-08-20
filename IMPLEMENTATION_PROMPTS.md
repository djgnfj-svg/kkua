# 끄아(KKUA) V2 구현을 위한 AI 개발자 프롬프트

## 프로젝트 개요 프롬프트

당신은 **끄아(KKUA)**라는 실시간 멀티플레이어 한국어 끝말잇기 게임을 **완전히 새로운 Pure WebSocket 아키텍처**로 구현해야 합니다.

### 핵심 요구사항
1. **Pure WebSocket 아키텍처**: 모든 실시간 통신은 WebSocket으로 처리
2. **이벤트 기반 상태 관리**: 서버가 모든 상태를 관리하고 클라이언트는 이벤트만 발송
3. **단일 진실의 원천**: Redis가 실시간 상태, PostgreSQL이 영구 데이터 담당
4. **포괄적인 기능**: 아이템 시스템, 단어 검증, 실시간 타이머, 게임 리포트, 로깅

### 기술 스택
- **백엔드**: Python FastAPI, WebSocket, Redis, PostgreSQL, SQLAlchemy
- **프론트엔드**: React, Zustand, WebSocket, TailwindCSS
- **배포**: Docker Compose

## 단계별 구현 프롬프트

### Phase 1: 백엔드 핵심 인프라 구축

**프롬프트:**
```
ARCHITECTURE_V2.md를 참조하여 다음을 구현하세요:

1. **데이터베이스 스키마 생성**
   - PostgreSQL 테이블 생성 (users, game_rooms, game_sessions, korean_dictionary, items, user_items, game_logs, word_submissions)
   - 모든 인덱스와 관계 설정
   - 샘플 한국어 단어 데이터 1000개 이상 삽입

2. **Redis 데이터 구조 설계**
   - 게임 룸 상태 구조 구현
   - 사용자 세션 관리 구조
   - 타이머 데이터 구조

3. **SQLAlchemy 모델 구현**
   - models/ 디렉토리에 모든 데이터베이스 모델 생성
   - Pydantic 스키마 정의
   - 관계 설정 및 검증 로직

**주의사항:**
- 모든 테이블에 적절한 인덱스 생성
- JSON 필드는 JSONB 타입 사용
- 외래 키 제약 조건 설정
- 한국어 단어는 UTF-8 인코딩 확인

**완료 조건:**
- 데이터베이스 마이그레이션 성공
- 모든 모델 테스트 통과
- 샘플 데이터 삽입 확인
```

### Phase 2: WebSocket 인프라 구축

**프롬프트:**
```
ARCHITECTURE_V2.md의 WebSocket 메시지 프로토콜을 정확히 구현하세요:

1. **연결 관리자 구현** (websocket/connection_manager.py)
   - 사용자별 WebSocket 연결 추적
   - 룸별 연결 그룹핑
   - 자동 연결 해제 처리
   - JWT 토큰 기반 인증

2. **메시지 라우터 구현** (websocket/message_router.py)
   - 메시지 타입별 핸들러 매핑
   - 입력 검증 및 에러 처리
   - 비동기 메시지 처리

3. **게임 이벤트 핸들러** (websocket/game_handler.py)
   - join_game, start_game, submit_word, use_item, forfeit_game 처리
   - 모든 클라이언트 메시지에 대한 서버 응답 구현

**필수 구현 메시지 타입:**
- 클라이언트 → 서버: join_game, start_game, submit_word, use_item, forfeit_game
- 서버 → 클라이언트: game_state_update, word_result, timer_update, item_used, game_finished, error

**주의사항:**
- 모든 메시지는 JSON 형태
- 에러 처리 및 로깅 필수
- 연결 끊김 시 자동 정리
- 메시지 타입 검증 엄격하게

**완료 조건:**
- WebSocket 연결/해제 테스트 성공
- 모든 메시지 타입 처리 확인
- 에러 케이스 처리 검증
```

### Phase 3: 게임 엔진 및 핵심 서비스

**프롬프트:**
```
게임의 핵심 로직을 구현하세요:

1. **게임 엔진 구현** (services/game_engine.py)
   - 게임 시작/종료 로직
   - 턴 관리 및 플레이어 순서
   - 라운드 진행 로직
   - 승리 조건 검사

2. **단어 검증 서비스** (services/word_validator.py)
   - 한국어 단어 유효성 검증
   - 끝말잇기 규칙 확인 (마지막 글자 = 첫 글자)
   - 중복 사용 단어 검사
   - 단어 정보 조회 (정의, 난이도, 점수)
   - Redis 캐싱 적용

3. **실시간 타이머 서비스** (services/timer_service.py)
   - 턴별 시간 제한 관리
   - 비동기 타이머 구현
   - 타이머 만료 시 자동 턴 넘김
   - 아이템으로 시간 연장/단축

4. **점수 계산 서비스** (services/score_calculator.py)
   - 기본 점수: 글자 수 × 난이도
   - 속도 보너스: 빠른 응답 시 추가 점수
   - 콤보 시스템: 연속 성공 시 배수 적용
   - 단어 희귀도에 따른 추가 점수

**점수 계산 공식:**
```python
base_score = len(word) * difficulty_multiplier
speed_bonus = max(0, (30 - response_time_seconds) * 2)
combo_bonus = current_combo * 10
rarity_bonus = rarity_score_map[word]
total_score = (base_score + speed_bonus + rarity_bonus) * combo_multiplier
```

**주의사항:**
- 모든 서비스는 비동기 구현
- Redis와 PostgreSQL 모두 활용
- 에러 발생 시 게임 상태 복구 가능
- 로깅 및 모니터링 포함

**완료 조건:**
- 완전한 게임 플레이 가능
- 점수 계산 정확성 검증
- 타이머 정확도 테스트
- 단어 검증 성능 테스트
```

### Phase 4: 아이템 시스템 구현

**프롬프트:**
```
게임 내 아이템 시스템을 완전히 구현하세요:

1. **아이템 시스템 서비스** (services/item_system.py)
   - 5가지 희귀도: common, uncommon, rare, epic, legendary
   - 아이템 타입별 효과 구현:
     - time_boost: 턴 시간 10초 연장
     - score_multiplier: 다음 단어 점수 2배
     - word_hint: 다음에 올 수 있는 글자 힌트
     - freeze_opponent: 상대방 시간 5초 단축
     - shield: 한 턴 동안 아이템 공격 무효화

2. **사용자 인벤토리 관리**
   - 아이템 획득 로직 (게임 종료 시 랜덤 지급)
   - 아이템 사용 쿨다운 관리
   - 아이템 효과 중첩 처리

3. **아이템 효과 적용**
   - 실시간으로 게임 상태에 반영
   - 다른 플레이어에게 효과 알림
   - 효과 지속 시간 관리

**아이템 데이터 예시:**
```json
{
  "time_boost": {
    "name": "시간 연장",
    "description": "턴 시간을 10초 연장합니다",
    "rarity": "common",
    "effect_type": "timer_extend",
    "effect_value": {"seconds": 10},
    "cooldown_seconds": 30
  },
  "word_hint": {
    "name": "글자 힌트",
    "description": "다음에 올 수 있는 글자를 알려줍니다",
    "rarity": "rare",
    "effect_type": "hint_next_word",
    "effect_value": {"hint_count": 3},
    "cooldown_seconds": 60
  }
}
```

**주의사항:**
- 아이템 효과는 즉시 반영되어야 함
- 모든 플레이어에게 아이템 사용 알림
- 아이템 남용 방지 (쿨다운, 사용 제한)
- 게임 밸런스 고려

**완료 조건:**
- 모든 아이템 효과 정상 작동
- 인벤토리 관리 시스템 완성
- 아이템 사용 로그 기록
```

### Phase 5: 게임 리포트 및 로깅 시스템

**프롬프트:**
```
게임 데이터 수집 및 리포트 생성 시스템을 구현하세요:

1. **게임 로깅 서비스** (services/game_logger.py)
   - 모든 게임 이벤트 실시간 로깅
   - 성능 메트릭 수집 (응답 시간, 메모리 사용량)
   - 배치 처리로 데이터베이스 저장 최적화

2. **리포트 생성 서비스** (services/report_generator.py)
   - 게임 종료 시 상세 리포트 생성
   - 개인 통계 및 성과 분석
   - 게임별 하이라이트 추출

**게임 리포트 포함 내용:**
```json
{
  "game_summary": {
    "session_id": "uuid",
    "duration_ms": 480000,
    "total_rounds": 12,
    "total_words": 48,
    "winner": {"user_id": 123, "nickname": "player1"}
  },
  "player_stats": [
    {
      "user_id": 123,
      "nickname": "player1",
      "total_score": 1250,
      "words_submitted": 15,
      "avg_response_time_ms": 8500,
      "items_used": 3,
      "max_combo": 5,
      "accuracy_rate": 0.93
    }
  ],
  "word_history": [
    {
      "round": 1,
      "user_id": 123,
      "word": "사과",
      "response_time_ms": 5500,
      "score": 120,
      "is_valid": true
    }
  ],
  "highlights": [
    {
      "type": "longest_word",
      "user_id": 456,
      "word": "프로그래밍",
      "score": 280
    },
    {
      "type": "fastest_response",
      "user_id": 123,
      "response_time_ms": 2300,
      "word": "컴퓨터"
    }
  ]
}
```

**로깅 이벤트 타입:**
- GAME_STARTED, GAME_FINISHED
- WORD_SUBMITTED, WORD_VALIDATED  
- ITEM_USED, ITEM_RECEIVED
- TURN_STARTED, TURN_TIMEOUT
- PLAYER_JOINED, PLAYER_LEFT

**주의사항:**
- 개인정보 보호 준수
- 로그 데이터 압축 및 보관 정책
- 실시간 처리 vs 배치 처리 구분
- 에러 로그와 게임 로그 분리

**완료 조건:**
- 모든 게임 이벤트 로깅
- 상세한 게임 리포트 생성
- 로그 성능 최적화 확인
```

### Phase 6: 프론트엔드 구현

**프롬프트:**
```
React 기반 프론트엔드를 구현하세요:

1. **WebSocket 통신 훅** (hooks/useGameWebSocket.js)
   - 자동 재연결 기능 (exponential backoff)
   - 메시지 큐 관리
   - 연결 상태 추적
   - 에러 처리

2. **게임 상태 관리** (stores/gameStore.js)
   - Zustand를 사용한 전역 상태 관리
   - 서버 상태와 클라이언트 상태 동기화
   - 낙관적 업데이트와 서버 검증

3. **핵심 게임 컴포넌트**
   - GameBoard: 게임 진행 상황 표시
   - WordInput: 단어 입력 인터페이스
   - Timer: 실시간 타이머 (초 단위)
   - PlayerList: 플레이어 목록 및 점수
   - ItemPanel: 아이템 사용 인터페이스
   - GameReport: 게임 종료 후 상세 리포트

**WebSocket 훅 구조:**
```javascript
const useGameWebSocket = (roomId) => {
  const [socket, setSocket] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [messageHistory, setMessageHistory] = useState([]);
  
  const sendMessage = useCallback((message) => {
    // 메시지 전송 로직
  }, [socket]);
  
  return {
    socket,
    connectionStatus,
    messageHistory,
    sendMessage,
    reconnect: () => {/* 재연결 로직 */}
  };
};
```

**상태 관리 구조:**
```javascript
const useGameStore = create((set, get) => ({
  gameState: null,
  players: [],
  currentTurn: 0,
  timer: 0,
  wordChain: [],
  myItems: [],
  
  // Actions
  updateGameState: (newState) => set({ gameState: newState }),
  submitWord: async (word) => {/* WebSocket으로 단어 제출 */},
  useItem: async (itemId, targetUserId) => {/* 아이템 사용 */},
}));
```

**주의사항:**
- 모든 UI는 반응형 디자인 (TailwindCSS)
- 접근성 고려 (키보드 탐색, 스크린 리더)
- 실시간 업데이트 시 부드러운 애니메이션
- 오프라인 상태 처리

**완료 조건:**
- 모든 게임 기능 UI 완성
- WebSocket 실시간 통신 검증
- 다양한 화면 크기 테스트
- 사용자 경험 최적화
```

### Phase 7: 성능 최적화 및 테스트

**프롬프트:**
```
시스템 성능 최적화 및 종합 테스트를 수행하세요:

1. **성능 최적화**
   - Redis 연결 풀링 최적화
   - WebSocket 메시지 배치 처리
   - 데이터베이스 쿼리 최적화
   - 프론트엔드 렌더링 최적화

2. **부하 테스트**
   - 동시 접속자 1000명 테스트
   - 동시 게임 룸 100개 테스트
   - 메모리 누수 검사
   - 데이터베이스 성능 측정

3. **통합 테스트**
   - 전체 게임 플로우 테스트
   - 다양한 에러 시나리오 테스트
   - 네트워크 끊김 상황 테스트
   - 동시성 문제 검증

**테스트 시나리오:**
```python
# 부하 테스트 예시
async def test_concurrent_games():
    """100개 게임룸에서 동시 게임 진행"""
    tasks = []
    for i in range(100):
        task = simulate_full_game(room_id=f"room_{i}", players=4)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    assert all(result.success for result in results)

async def test_websocket_resilience():
    """WebSocket 연결 끊김 및 재연결 테스트"""
    # 연결 강제 종료 후 자동 재연결 확인
```

**모니터링 메트릭:**
- WebSocket 연결 수
- 평균 응답 시간
- 메모리 사용량
- CPU 사용률
- 데이터베이스 연결 수
- Redis 메모리 사용량

**주의사항:**
- 프로덕션 환경과 유사한 조건에서 테스트
- 모든 에러 케이스 커버
- 성능 저하 원인 식별 및 해결
- 자동화된 테스트 스크립트 작성

**완료 조건:**
- 모든 부하 테스트 통과
- 성능 요구사항 달성
- 안정성 검증 완료
- 배포 준비 완료
```

## 중요 구현 지침

### 1. 코드 품질 기준
- **타입 힌팅**: 모든 Python 함수에 타입 힌트 추가
- **에러 처리**: 모든 예외 상황 처리 및 적절한 에러 메시지
- **로깅**: 중요한 이벤트는 모두 로그 기록
- **문서화**: 모든 함수와 클래스에 docstring 작성

### 2. 보안 요구사항
- **입력 검증**: 모든 사용자 입력 철저히 검증
- **SQL 인젝션 방지**: SQLAlchemy ORM 사용
- **XSS 방지**: 사용자 입력 sanitization
- **인증**: JWT 토큰 기반 인증 구현
- **권한**: 게임 액션 권한 확인

### 3. 성능 요구사항
- **응답 시간**: API 응답 시간 100ms 이하
- **동시 접속**: 1000명 이상 동시 접속 지원
- **메모리**: 서버 메모리 사용량 2GB 이하
- **데이터베이스**: 쿼리 응답 시간 50ms 이하

### 4. 테스트 요구사항
- **단위 테스트**: 모든 서비스 함수 테스트
- **통합 테스트**: API 엔드포인트 테스트
- **E2E 테스트**: 전체 게임 플로우 테스트
- **커버리지**: 코드 커버리지 90% 이상

## 단계별 검증 체크리스트

### Phase 1 완료 확인
- [ ] 데이터베이스 스키마 생성 완료
- [ ] 모든 테이블 관계 설정 확인
- [ ] 1000개 이상 한국어 단어 데이터 삽입
- [ ] SQLAlchemy 모델 테스트 통과

### Phase 2 완료 확인
- [ ] WebSocket 연결/해제 정상 동작
- [ ] JWT 토큰 인증 구현
- [ ] 모든 메시지 타입 처리 확인
- [ ] 에러 처리 및 로깅 구현

### Phase 3 완료 확인
- [ ] 완전한 게임 플레이 가능
- [ ] 단어 검증 로직 정확성 확인
- [ ] 실시간 타이머 정확도 검증
- [ ] 점수 계산 공식 정확성 확인

### Phase 4 완료 확인
- [ ] 모든 아이템 효과 정상 작동
- [ ] 아이템 쿨다운 시스템 구현
- [ ] 인벤토리 관리 완성
- [ ] 아이템 밸런스 검증

### Phase 5 완료 확인
- [ ] 모든 게임 이벤트 로깅
- [ ] 상세한 게임 리포트 생성
- [ ] 배치 처리 성능 최적화
- [ ] 로그 저장 및 조회 시스템

### Phase 6 완료 확인
- [ ] 모든 게임 UI 컴포넌트 완성
- [ ] WebSocket 실시간 통신 구현
- [ ] 반응형 디자인 적용
- [ ] 사용자 경험 최적화

### Phase 7 완료 확인
- [ ] 1000명 동시 접속 테스트 통과
- [ ] 100개 동시 게임룸 테스트 통과
- [ ] 모든 에러 시나리오 테스트 완료
- [ ] 성능 요구사항 달성

## 최종 배포 준비

### 환경 설정
- Docker Compose 파일 완성
- 환경 변수 설정 (.env 파일)
- 프로덕션 설정 분리
- SSL 인증서 설정

### 모니터링 설정
- 로그 수집 시스템
- 메트릭 모니터링
- 알람 시스템
- 헬스 체크 엔드포인트

이 프롬프트를 단계별로 따라 구현하면 완전한 끄아(KKUA) V2 시스템을 구축할 수 있습니다. 각 단계에서 검증 체크리스트를 확인하여 누락된 기능이 없도록 주의하세요.