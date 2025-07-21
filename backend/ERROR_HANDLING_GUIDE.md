# Error Handling Improvement Guide

## 🎯 개선 목표

현재 코드베이스의 `except Exception:` 패턴을 구체적이고 의미있는 예외 처리로 개선합니다.

## 🔧 개선 패턴

### 1. Redis Service 에러 처리 패턴

**기존 (문제 있음):**
```python
except Exception as e:
    logger.error(f"게임 생성 실패: {e}")
    return False
```

**개선된 패턴:**
```python
except (ConnectionError, TimeoutError) as e:
    logger.error(f"Redis 연결 오류로 게임 생성 실패: room_id={room_id}, error={e}")
    return False
except (ResponseError, RedisError) as e:
    logger.error(f"Redis 서버 오류로 게임 생성 실패: room_id={room_id}, error={e}")
    return False
except (ValueError, KeyError) as e:
    logger.error(f"잘못된 데이터로 게임 생성 실패: room_id={room_id}, error={e}")
    return False
except Exception as e:
    logger.error(f"예상치 못한 게임 생성 실패: room_id={room_id}, error={e}", exc_info=True)
    return False
```

### 2. Database Repository 에러 처리 패턴

**기존 (문제 있음):**
```python
except Exception as e:
    logging.error(f"게스트 ID 검색 중 오류 발생: {str(e)}")
    return None
```

**개선된 패턴:**
```python
except SQLAlchemyError as e:
    logger.error(f"Database error while finding guest by ID {guest_id}: {e}")
    self.db.rollback()
    return None
except ValueError as e:
    logger.warning(f"Invalid guest_id parameter: {guest_id}, error: {e}")
    return None
except Exception as e:
    logger.error(f"Unexpected error finding guest {guest_id}: {e}", exc_info=True)
    self.db.rollback()
    return None
```

### 3. API Router 에러 처리 패턴

**기존 (문제 있음):**
```python
except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"단어 제출 처리 중 오류: {str(e)}"
    )
```

**개선된 패턴:**
```python
except RedisError as e:
    logger.error(f"Redis error during word submission: {e}")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="게임 서버 연결 오류"
    )
except ValidationError as e:
    logger.warning(f"Word validation error: {e}")
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="유효하지 않은 단어입니다"
    )
except ValueError as e:
    logger.warning(f"Invalid game state: {e}")
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="잘못된 게임 상태"
    )
except Exception as e:
    logger.error(f"Unexpected error in word submission: {e}", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="단어 제출 처리 중 예상치 못한 오류"
    )
```

### 4. WebSocket 에러 처리 패턴

**기존 (문제 있음):**
```python
try:
    await websocket.close(code=4003, reason=f"오류 발생: {str(e)}")
except Exception:
    pass
```

**개선된 패턴:**
```python
try:
    await websocket.close(code=4003, reason=f"오류 발생: {str(e)}")
except (ConnectionClosed, RuntimeError) as e:
    logger.debug(f"WebSocket already closed: {e}")
except Exception as e:
    logger.error(f"Error closing WebSocket connection: {e}", exc_info=True)
```

## 📋 개선이 필요한 파일 목록

### 🚨 High Priority (즉시 수정 필요)

1. **`backend/services/redis_game_service.py`** - 25+ instances
   - 모든 Redis 연결 및 데이터 처리
   - 게임 상태 관리 메서드들

2. **`backend/repositories/guest_repository.py`** - 2 instances
   - 데이터베이스 접근 메서드들

3. **`backend/services/gameroom_service.py`** - 15+ instances  
   - 게임룸 관리 및 액션 처리

4. **`backend/routers/game_api_router.py`** - 4 instances
   - API 엔드포인트들

### ⚠️ Medium Priority

5. **`backend/routers/gameroom_ws_router.py`** - 3 instances
6. **`backend/services/websocket_message_service.py`** - 6 instances
7. **`backend/services/game_data_persistence_service.py`** - 6 instances

## 🛠️ 권장 Import 추가

각 파일 상단에 필요한 예외 클래스들을 import하세요:

```python
# Redis exceptions
from redis.exceptions import (
    RedisError, ConnectionError, TimeoutError, 
    ResponseError, BusyLoadingError, ReadOnlyError
)

# Database exceptions
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError

# FastAPI exceptions
from fastapi import HTTPException
from pydantic import ValidationError

# WebSocket exceptions
from fastapi.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosed

# Standard logging
import logging
logger = logging.getLogger(__name__)
```

## ✅ 개선 체크리스트

각 파일을 개선할 때 다음 사항을 확인하세요:

- [ ] **구체적인 예외 타입 사용**: `Exception` 대신 구체적인 예외 클래스
- [ ] **적절한 로그 레벨**: 
  - `logger.error()`: 예상치 못한 오류
  - `logger.warning()`: 예상 가능한 오류
  - `logger.info()`: 정상 처리
- [ ] **컨텍스트 정보 포함**: 함수명, 매개변수, 상태 정보
- [ ] **exc_info=True 사용**: 예상치 못한 오류에서 전체 스택 트레이스
- [ ] **사용자 친화적 메시지**: API 응답에서 내부 오류 정보 숨김
- [ ] **데이터베이스 롤백**: DB 오류 발생 시 트랜잭션 롤백
- [ ] **리소스 정리**: 연결, 파일, 태스크 등 적절한 정리

## 🔄 점진적 개선 전략

1. **Phase 1**: High Priority 파일들부터 개선
2. **Phase 2**: Medium Priority 파일들 개선  
3. **Phase 3**: 테스트 코드와 함께 검증
4. **Phase 4**: 모니터링 및 로그 분석으로 개선 효과 확인

## 📊 개선 효과

예외 처리 개선 후 기대 효과:

- **🔍 디버깅 향상**: 구체적인 오류 정보로 문제 원인 파악 용이
- **🛡️ 안정성 증대**: 예상치 못한 오류에서 시스템 보호
- **📈 모니터링 개선**: 로그 분석을 통한 시스템 상태 파악
- **👥 사용자 경험**: 의미있는 오류 메시지로 UX 개선
- **🚀 유지보수성**: 코드 가독성 및 유지보수 편의성 향상

---

**💡 팁**: 한 번에 모든 파일을 수정하기보다는, 파일별로 단계적으로 개선하여 테스트와 함께 진행하는 것을 권장합니다.