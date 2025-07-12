# API 문서

## 개요

KKUA 백엔드는 RESTful API와 WebSocket을 제공합니다. 모든 API는 세션 기반 인증을 사용하며, HTTP-only 쿠키를 통해 세션을 관리합니다.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## 인증

### 세션 기반 인증
- 로그인 시 `session_token` 쿠키가 설정됩니다
- 보호된 엔드포인트는 이 쿠키를 검증합니다
- 쿠키는 HTTP-only이므로 JavaScript에서 직접 접근할 수 없습니다

## API 응답 형식

### 성공 응답
```json
{
  "status": "success",
  "data": {
    // 응답 데이터
  },
  "message": "선택적 메시지"
}
```

### 에러 응답
```json
{
  "detail": "에러 메시지",
  "status_code": 400
}
```

## 인증 API

### POST /auth/login
닉네임으로 로그인 (게스트 계정 생성/조회)

**Request Body:**
```json
{
  "nickname": "사용자닉네임"
}
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "guest_id": 123,
    "nickname": "사용자닉네임",
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-01-01T12:00:00Z"
  },
  "message": "로그인 성공"
}
```

**Cookies Set:**
- `session_token`: HttpOnly, Secure, SameSite=Lax

### POST /auth/logout
로그아웃 및 세션 정리

**Response (200):**
```json
{
  "status": "success",
  "message": "로그아웃 완료"
}
```

**Cookies Cleared:**
- `session_token` 삭제

### GET /auth/me
현재 사용자 프로필 조회 (인증 필요)

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "guest_id": 123,
    "nickname": "사용자닉네임",
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

### PUT /auth/me
사용자 프로필 업데이트 (인증 필요)

**Request Body:**
```json
{
  "nickname": "새닉네임"
}
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "guest_id": 123,
    "nickname": "새닉네임",
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-01-01T12:00:00Z"
  },
  "message": "프로필이 업데이트되었습니다"
}
```

### GET /auth/status
인증 상태 확인

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "is_authenticated": true,
    "guest_id": 123
  }
}
```

## 게임방 API

### GET /gamerooms
게임방 목록 조회

**Query Parameters:**
- `limit` (optional, default=10): 조회할 방 개수
- `offset` (optional, default=0): 시작 위치
- `status` (optional): 방 상태 필터 (WAITING, PLAYING, FINISHED)

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "rooms": [
      {
        "room_id": 1,
        "title": "재미있는 끝말잇기",
        "max_players": 8,
        "participant_count": 3,
        "status": "WAITING",
        "game_mode": "standard",
        "time_limit": 300,
        "room_type": "normal",
        "created_by": 123,
        "created_at": "2024-01-01T12:00:00Z"
      }
    ],
    "total": 25,
    "limit": 10,
    "offset": 0
  }
}
```

### POST /gamerooms
새 게임방 생성 (인증 필요)

**Request Body:**
```json
{
  "title": "내 게임방",
  "max_players": 6,
  "game_mode": "standard",
  "time_limit": 300,
  "room_type": "normal"
}
```

**Response (201):**
```json
{
  "status": "success",
  "data": {
    "room_id": 10,
    "title": "내 게임방",
    "max_players": 6,
    "participant_count": 1,
    "status": "WAITING",
    "game_mode": "standard",
    "time_limit": 300,
    "room_type": "normal",
    "created_by": 123,
    "created_at": "2024-01-01T12:00:00Z"
  },
  "message": "게임방이 생성되었습니다"
}
```

### GET /gamerooms/{room_id}
특정 게임방 정보 조회

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "room": {
      "room_id": 1,
      "title": "재미있는 끝말잇기",
      "max_players": 8,
      "participant_count": 3,
      "status": "WAITING",
      "game_mode": "standard",
      "time_limit": 300,
      "room_type": "normal",
      "created_by": 123,
      "created_at": "2024-01-01T12:00:00Z"
    },
    "participants": [
      {
        "guest_id": 123,
        "nickname": "방장님",
        "is_creator": true,
        "joined_at": "2024-01-01T12:00:00Z",
        "status": "READY",
        "is_ready": true
      },
      {
        "guest_id": 456,
        "nickname": "참가자1",
        "is_creator": false,
        "joined_at": "2024-01-01T12:05:00Z",
        "status": "WAITING",
        "is_ready": false
      }
    ]
  }
}
```

### DELETE /gamerooms/{room_id}
게임방 삭제 (방장만 가능, 인증 필요)

**Response (200):**
```json
{
  "status": "success",
  "message": "게임방이 삭제되었습니다"
}
```

## 게임방 액션 API

### POST /gamerooms/{room_id}/join
게임방 참가 (인증 필요)

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "participant_id": 789,
    "guest_id": 456,
    "room_id": 1,
    "joined_at": "2024-01-01T12:10:00Z",
    "status": "WAITING",
    "is_creator": false
  },
  "message": "게임방에 참가했습니다"
}
```

### POST /gamerooms/{room_id}/leave
게임방 나가기 (인증 필요)

**Response (200):**
```json
{
  "status": "success",
  "message": "게임방에서 나갔습니다"
}
```

### POST /gamerooms/{room_id}/ready
준비 상태 토글 (인증 필요)

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "is_ready": true
  },
  "message": "준비 상태가 변경되었습니다"
}
```

### POST /gamerooms/{room_id}/start
게임 시작 (방장만 가능, 인증 필요)

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "room_id": 1,
    "game_status": "PLAYING"
  },
  "message": "게임이 시작되었습니다"
}
```

### POST /gamerooms/{room_id}/end
게임 종료 (방장만 가능, 인증 필요)

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "room_id": 1,
    "game_status": "FINISHED",
    "winner": "승리자닉네임",
    "result_available": true
  },
  "message": "게임이 종료되었습니다"
}
```

### GET /gamerooms/{room_id}/result
게임 결과 조회

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "game_log_id": 42,
    "room_id": 1,
    "winner_name": "승리자닉네임",
    "started_at": "2024-01-01T12:00:00Z",
    "ended_at": "2024-01-01T12:15:00Z",
    "total_rounds": 15,
    "game_duration": "15분 30초",
    "total_words": 15,
    "average_response_time": 4.2,
    "longest_word": "프로그래밍",
    "fastest_response": 2.1,
    "slowest_response": 8.5,
    "mvp_name": "MVP닉네임",
    "players": [
      {
        "guest_id": 123,
        "nickname": "플레이어1",
        "words_submitted": 8,
        "total_score": 24,
        "average_response_time": 3.2,
        "longest_word": "컴퓨터과학",
        "rank": 1
      }
    ],
    "used_words": [
      {
        "word": "사과",
        "player_nickname": "플레이어1",
        "submitted_at": "2024-01-01T12:01:00Z",
        "response_time": 3.2,
        "is_valid": true
      }
    ]
  }
}
```

## 게스트 관리 API

### GET /guests
모든 게스트 목록 조회

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "guests": [
      {
        "guest_id": 123,
        "nickname": "사용자1",
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "created_at": "2024-01-01T12:00:00Z"
      }
    ]
  }
}
```

### GET /guests/{guest_id}
특정 게스트 정보 조회

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "guest_id": 123,
    "nickname": "사용자1",
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

## WebSocket API

### 연결
```
ws://localhost:8000/ws/gamerooms/{room_id}
```

**인증**: 연결 시 HTTP 헤더의 쿠키에서 session_token 검증

### 메시지 타입

#### 1. 채팅 메시지

**클라이언트 → 서버:**
```json
{
  "type": "chat",
  "message": "안녕하세요!",
  "message_id": "123-1704110400000"
}
```

**서버 → 클라이언트:**
```json
{
  "type": "chat",
  "guest_id": 123,
  "nickname": "사용자1",
  "message": "안녕하세요!",
  "timestamp": "2024-01-01T12:00:00Z",
  "message_id": "123-1704110400000"
}
```

#### 2. 게임 액션

**클라이언트 → 서버:**
```json
{
  "type": "game_action",
  "action": "toggle_ready"
}
```

**서버 → 클라이언트:**
```json
{
  "type": "ready_status_changed",
  "guest_id": 123,
  "nickname": "사용자1",
  "is_ready": true,
  "message": "사용자1님이 준비되었습니다"
}
```

#### 3. 참가자 업데이트

**서버 → 클라이언트:**
```json
{
  "type": "participants_update",
  "participants": [
    {
      "guest_id": 123,
      "nickname": "사용자1",
      "is_creator": true,
      "joined_at": "2024-01-01T12:00:00Z",
      "status": "READY",
      "is_ready": true
    }
  ],
  "message": "사용자2님이 방에 참가했습니다"
}
```

#### 4. 게임 상태 변경

**서버 → 클라이언트:**
```json
{
  "type": "game_started",
  "room_id": 1,
  "message": "게임이 시작되었습니다!"
}
```

```json
{
  "type": "game_ended",
  "room_id": 1,
  "winner": "승리자닉네임",
  "message": "게임이 종료되었습니다"
}
```

#### 5. 끝말잇기 게임

**클라이언트 → 서버:**
```json
{
  "type": "word_chain",
  "word": "사과",
  "timestamp": 1704110400000
}
```

**서버 → 클라이언트:**
```json
{
  "type": "word_chain_update",
  "current_player_id": 456,
  "last_word": "사과",
  "last_character": "과",
  "used_words": ["사과"],
  "valid": true,
  "message": "단어가 승인되었습니다",
  "next_player": "다음플레이어"
}
```

#### 6. 시스템 메시지

**서버 → 클라이언트:**
```json
{
  "type": "system",
  "message": "시스템 알림 메시지",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 에러 코드

### HTTP 상태 코드

- `200`: 성공
- `201`: 생성 성공
- `400`: 잘못된 요청
- `401`: 인증 필요
- `403`: 권한 없음
- `404`: 리소스 없음
- `409`: 충돌 (이미 존재)
- `500`: 서버 오류

### 커스텀 에러 메시지

```json
{
  "detail": "이미 해당 게임방에 참가 중입니다",
  "status_code": 409
}
```

```json
{
  "detail": "게임방이 가득 찼습니다",
  "status_code": 400
}
```

```json
{
  "detail": "방장만 게임을 시작할 수 있습니다",
  "status_code": 403
}
```

## Rate Limiting

### API 제한
- 인증 API: 10 requests/minute per IP
- 일반 API: 100 requests/minute per user
- WebSocket 메시지: 30 messages/minute per user

### 제한 초과 시 응답
```json
{
  "detail": "Rate limit exceeded. Try again later.",
  "status_code": 429
}
```

## 개발자 도구

### API 문서
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### 헬스 체크
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0"
}
```