# Redis 아키텍처 개선 방안

## 🚨 현재 문제점

### 1. Redis 키 구조 문제
```
현재: game:{room_id}:player:{guest_id}
문제: 같은 사용자가 여러 방에 참여하면 데이터 충돌
```

### 2. 데이터 정리 타이밍 문제
- `end_game()`: 즉시 Redis 데이터 삭제 → 게임 결과 조회 불가
- `complete_game()`: 데이터 유지하려다 주석 처리 → 메모리 누수

### 3. 동시 게임 참여 시 데이터 충돌
- 사용자가 방 A에서 게임 중인데 방 B 참여 시 데이터 덮어쓰기

## 🔧 적용된 개선사항

### 1. 지연 정리 시스템
```python
# 즉시 정리 → 30분 지연 정리로 변경
asyncio.create_task(self._delayed_cleanup(redis_game, room_id, delay_minutes=30))
```

### 2. 플레이어 활성 게임 검증
```python
async def check_player_active_games(self, guest_id: int) -> List[int]:
    """플레이어가 참여 중인 활성 게임 목록 조회"""

async def validate_player_can_join(self, room_id: int, guest_id: int) -> tuple[bool, str]:
    """플레이어가 게임에 참여할 수 있는지 검증"""
```

### 3. 게임 데이터 유효성 검증
```python
async def get_player_stats(self, room_id: int, guest_id: int) -> Optional[Dict]:
    # 게임 상태 먼저 확인
    # 해당 플레이어가 이 게임의 참가자인지 확인
```

### 4. 게임 생성 시 기존 데이터 정리
```python
async def create_game(self, room_id: int, participants: List[Dict], settings: Dict = None) -> bool:
    # 기존 게임 데이터가 있다면 정리
    await self.cleanup_game(room_id)
```

## 🏗️ 향후 개선 방안 (선택사항)

### 1. 개선된 Redis 키 구조
```
현재: game:{room_id}:player:{guest_id}
개선: game:{room_id}:session:{session_id}:player:{guest_id}
```

### 2. 게임 세션 관리
```python
# 게임 시작 시 고유 세션 ID 생성
session_id = f"{room_id}_{int(time.time())}"
```

### 3. TTL 기반 자동 정리
```python
# 게임 종료 시 TTL 설정 (1시간)
await self.redis_client.expire(f"game:{room_id}*", 3600)
```

## 📊 모달 0점 문제 원인 분석

### 문제 재현 및 해결
1. **백엔드 API**: ✅ 정상 작동 확인
2. **Redis 데이터**: ✅ 정상 저장 확인  
3. **문제 원인**: 프론트엔드 모달이 API 데이터를 제대로 표시하지 못함

### 검증 결과
```bash
# Redis 실제 데이터
curl http://localhost:8000/gamerooms/11/test-redis
# 결과: score=40, words_submitted=1 (정상)

# API 응답 데이터  
curl -b cookies.txt http://localhost:8000/gamerooms/11/result
# 결과: total_score=40, words_submitted=1 (정상)

# 결론: 백엔드는 정상, 프론트엔드 모달 수정 필요
```

## ✅ 현재 해결된 문제들

1. **데이터 정리 타이밍**: 30분 지연 정리로 결과 조회 시간 확보
2. **중복 게임 참여 검증**: 플레이어의 다른 활성 게임 체크
3. **데이터 유효성 검증**: 게임-플레이어 관계 확인
4. **게임 생성 시 정리**: 기존 데이터 충돌 방지

## 🎯 다음 단계

1. **프론트엔드 모달 수정**: 게임 결과 API 데이터를 올바르게 표시
2. **Redis 모니터링**: 메모리 사용량 및 TTL 관리
3. **에러 핸들링**: 동시 접근 및 네트워크 오류 대응