# 데이터베이스 스키마

## 개요

KKUA 프로젝트는 PostgreSQL을 사용하며, SQLAlchemy ORM을 통해 데이터베이스와 상호작용합니다. 스키마는 게스트 관리, 게임방 운영, 게임 결과 추적을 위한 테이블들로 구성됩니다.

## 데이터베이스 설정

```python
# db/postgres.py
DATABASE_URL = "postgresql://postgres:mysecretpassword@db:5432/mydb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

## 테이블 스키마

### 1. guests (게스트/사용자)

```sql
CREATE TABLE guests (
    guest_id SERIAL PRIMARY KEY,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    nickname VARCHAR(50) UNIQUE NOT NULL,
    session_token VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_guests_uuid ON guests(uuid);
CREATE INDEX idx_guests_nickname ON guests(nickname);
CREATE INDEX idx_guests_session_token ON guests(session_token);
```

**SQLAlchemy 모델:**
```python
class Guest(Base):
    __tablename__ = "guests"
    
    guest_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    uuid = Column(String(36), unique=True, index=True, nullable=False)
    nickname = Column(String(50), unique=True, index=True, nullable=False)
    session_token = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    gamerooms = relationship("Gameroom", back_populates="creator")
    participations = relationship("GameroomParticipant", back_populates="guest")
    game_stats = relationship("PlayerGameStats", back_populates="player")
```

**용도:**
- 게스트 사용자 정보 저장
- 세션 토큰을 통한 인증 관리
- 닉네임 중복 방지

### 2. gamerooms (게임방)

```sql
CREATE TABLE gamerooms (
    room_id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    max_players INTEGER DEFAULT 8,
    participant_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'WAITING',
    game_mode VARCHAR(20) DEFAULT 'standard',
    time_limit INTEGER DEFAULT 300,
    room_type VARCHAR(20) DEFAULT 'normal',
    created_by INTEGER REFERENCES guests(guest_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    ended_at TIMESTAMP
);

CREATE INDEX idx_gamerooms_status ON gamerooms(status);
CREATE INDEX idx_gamerooms_created_by ON gamerooms(created_by);
CREATE INDEX idx_gamerooms_created_at ON gamerooms(created_at);
```

**SQLAlchemy 모델:**
```python
class GameStatus(Enum):
    WAITING = "WAITING"
    PLAYING = "PLAYING"
    FINISHED = "FINISHED"

class Gameroom(Base):
    __tablename__ = "gamerooms"
    
    room_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    max_players = Column(Integer, default=8)
    participant_count = Column(Integer, default=0)
    status = Column(String(20), default=GameStatus.WAITING.value, index=True)
    game_mode = Column(String(20), default="standard")
    time_limit = Column(Integer, default=300)
    room_type = Column(String(20), default="normal")
    created_by = Column(Integer, ForeignKey("guests.guest_id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    
    # 관계
    creator = relationship("Guest", back_populates="gamerooms")
    participants = relationship("GameroomParticipant", back_populates="gameroom")
    game_logs = relationship("GameLog", back_populates="room")
```

**필드 설명:**
- `status`: WAITING(대기), PLAYING(진행중), FINISHED(종료)
- `game_mode`: standard(일반), speed(빠른게임), challenge(도전모드)
- `room_type`: normal(일반방), private(비공개방)
- `time_limit`: 턴당 제한시간 (초)

### 3. gameroom_participants (게임방 참가자)

```sql
CREATE TABLE gameroom_participants (
    participant_id SERIAL PRIMARY KEY,
    room_id INTEGER REFERENCES gamerooms(room_id),
    guest_id INTEGER REFERENCES guests(guest_id),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'WAITING',
    is_creator BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_participants_room_id ON gameroom_participants(room_id);
CREATE INDEX idx_participants_guest_id ON gameroom_participants(guest_id);
CREATE INDEX idx_participants_active ON gameroom_participants(room_id, left_at) WHERE left_at IS NULL;
```

**SQLAlchemy 모델:**
```python
class ParticipantStatus(Enum):
    WAITING = "WAITING"
    READY = "READY"
    PLAYING = "PLAYING"
    LEFT = "LEFT"

class GameroomParticipant(Base):
    __tablename__ = "gameroom_participants"
    
    participant_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("gamerooms.room_id"), nullable=False, index=True)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False, index=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)
    status = Column(String(20), default=ParticipantStatus.WAITING.value)
    is_creator = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    gameroom = relationship("Gameroom", back_populates="participants")
    guest = relationship("Guest", back_populates="participations")
```

**특징:**
- Soft Delete 방식 사용 (`left_at` 필드)
- 활성 참가자는 `left_at IS NULL`로 필터링
- 방장 여부는 `is_creator` 필드로 관리

### 4. game_logs (게임 기록)

```sql
CREATE TABLE game_logs (
    id SERIAL PRIMARY KEY,
    room_id INTEGER REFERENCES gamerooms(room_id),
    winner_id INTEGER REFERENCES guests(guest_id),
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    total_rounds INTEGER DEFAULT 0,
    total_words INTEGER DEFAULT 0,
    average_response_time FLOAT,
    longest_word VARCHAR(100),
    fastest_response FLOAT,
    slowest_response FLOAT,
    mvp_id INTEGER REFERENCES guests(guest_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_game_logs_room_id ON game_logs(room_id);
CREATE INDEX idx_game_logs_winner_id ON game_logs(winner_id);
CREATE INDEX idx_game_logs_started_at ON game_logs(started_at);
```

**SQLAlchemy 모델:**
```python
class GameLog(Base):
    __tablename__ = "game_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("gamerooms.room_id"), nullable=False, index=True)
    winner_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    total_rounds = Column(Integer, default=0)
    total_words = Column(Integer, default=0)
    average_response_time = Column(Float, nullable=True)
    longest_word = Column(String(100), nullable=True)
    fastest_response = Column(Float, nullable=True)
    slowest_response = Column(Float, nullable=True)
    mvp_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    room = relationship("Gameroom", back_populates="game_logs")
    winner = relationship("Guest", foreign_keys=[winner_id])
    mvp = relationship("Guest", foreign_keys=[mvp_id])
    word_entries = relationship("WordChainEntry", back_populates="game_log")
    player_stats = relationship("PlayerGameStats", back_populates="game_log")
```

### 5. word_chain_entries (단어 입력 기록)

```sql
CREATE TABLE word_chain_entries (
    id SERIAL PRIMARY KEY,
    game_log_id INTEGER REFERENCES game_logs(id),
    player_id INTEGER REFERENCES guests(guest_id),
    word VARCHAR(100) NOT NULL,
    is_valid BOOLEAN DEFAULT TRUE,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_time FLOAT,
    round_number INTEGER,
    previous_character VARCHAR(10),
    ending_character VARCHAR(10)
);

CREATE INDEX idx_word_entries_game_log_id ON word_chain_entries(game_log_id);
CREATE INDEX idx_word_entries_player_id ON word_chain_entries(player_id);
CREATE INDEX idx_word_entries_round ON word_chain_entries(game_log_id, round_number);
```

**SQLAlchemy 모델:**
```python
class WordChainEntry(Base):
    __tablename__ = "word_chain_entries"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    game_log_id = Column(Integer, ForeignKey("game_logs.id"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False, index=True)
    word = Column(String(100), nullable=False)
    is_valid = Column(Boolean, default=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    response_time = Column(Float, nullable=True)
    round_number = Column(Integer, nullable=True)
    previous_character = Column(String(10), nullable=True)
    ending_character = Column(String(10), nullable=True)
    
    # 관계
    game_log = relationship("GameLog", back_populates="word_entries")
    player = relationship("Guest")
```

### 6. player_game_stats (플레이어 게임 통계)

```sql
CREATE TABLE player_game_stats (
    id SERIAL PRIMARY KEY,
    game_log_id INTEGER REFERENCES game_logs(id),
    player_id INTEGER REFERENCES guests(guest_id),
    words_submitted INTEGER DEFAULT 0,
    valid_words INTEGER DEFAULT 0,
    invalid_words INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0,
    average_response_time FLOAT,
    fastest_response FLOAT,
    slowest_response FLOAT,
    longest_word VARCHAR(100),
    rank INTEGER,
    bonus_points INTEGER DEFAULT 0
);

CREATE INDEX idx_player_stats_game_log_id ON player_game_stats(game_log_id);
CREATE INDEX idx_player_stats_player_id ON player_game_stats(player_id);
CREATE UNIQUE INDEX idx_player_stats_unique ON player_game_stats(game_log_id, player_id);
```

**SQLAlchemy 모델:**
```python
class PlayerGameStats(Base):
    __tablename__ = "player_game_stats"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    game_log_id = Column(Integer, ForeignKey("game_logs.id"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False, index=True)
    words_submitted = Column(Integer, default=0)
    valid_words = Column(Integer, default=0)
    invalid_words = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    average_response_time = Column(Float, nullable=True)
    fastest_response = Column(Float, nullable=True)
    slowest_response = Column(Float, nullable=True)
    longest_word = Column(String(100), nullable=True)
    rank = Column(Integer, nullable=True)
    bonus_points = Column(Integer, default=0)
    
    # 관계
    game_log = relationship("GameLog", back_populates="player_stats")
    player = relationship("Guest", back_populates="game_stats")
    
    # 유니크 제약 조건
    __table_args__ = (
        UniqueConstraint('game_log_id', 'player_id', name='_game_player_stats_uc'),
    )
```

## 관계도 (ERD)

```
guests (1) ────────── (*) gameroom_participants (*) ────────── (1) gamerooms
  │                                                                   │
  │                                                                   │
  │ (1:*)                                                        (1:*)│
  │                                                                   │
  └─── game_logs ──────────────────────────────────────────────────────┘
         │ (1:*)
         ├─── word_chain_entries
         │
         └─── player_game_stats
```

## 쿼리 예제

### 1. 활성 게임방 목록 조회

```python
def get_active_rooms(db: Session, limit: int = 10) -> List[Gameroom]:
    return (
        db.query(Gameroom)
        .filter(Gameroom.status.in_([GameStatus.WAITING.value, GameStatus.PLAYING.value]))
        .order_by(Gameroom.created_at.desc())
        .limit(limit)
        .all()
    )
```

### 2. 특정 방의 활성 참가자 조회

```python
def get_room_participants(db: Session, room_id: int) -> List[GameroomParticipant]:
    return (
        db.query(GameroomParticipant)
        .filter(
            GameroomParticipant.room_id == room_id,
            GameroomParticipant.left_at.is_(None)
        )
        .join(Guest)
        .order_by(GameroomParticipant.joined_at)
        .all()
    )
```

### 3. 게임 결과 상세 조회

```python
def get_game_result(db: Session, room_id: int) -> Optional[GameLog]:
    return (
        db.query(GameLog)
        .filter(GameLog.room_id == room_id)
        .options(
            joinedload(GameLog.winner),
            joinedload(GameLog.mvp),
            joinedload(GameLog.word_entries).joinedload(WordChainEntry.player),
            joinedload(GameLog.player_stats).joinedload(PlayerGameStats.player)
        )
        .order_by(GameLog.started_at.desc())
        .first()
    )
```

### 4. 플레이어 통계 조회

```python
def get_player_stats(db: Session, player_id: int, limit: int = 10):
    return (
        db.query(PlayerGameStats)
        .join(GameLog)
        .filter(PlayerGameStats.player_id == player_id)
        .order_by(GameLog.started_at.desc())
        .limit(limit)
        .all()
    )
```

### 5. 인기 단어 조회

```python
def get_popular_words(db: Session, limit: int = 20):
    return (
        db.query(
            WordChainEntry.word,
            func.count(WordChainEntry.id).label('usage_count')
        )
        .filter(WordChainEntry.is_valid == True)
        .group_by(WordChainEntry.word)
        .order_by(func.count(WordChainEntry.id).desc())
        .limit(limit)
        .all()
    )
```

## 인덱스 최적화

### 성능 중요 인덱스

```sql
-- 게임방 목록 조회 최적화
CREATE INDEX idx_gamerooms_status_created_at ON gamerooms(status, created_at DESC);

-- 활성 참가자 조회 최적화  
CREATE INDEX idx_participants_room_active ON gameroom_participants(room_id) WHERE left_at IS NULL;

-- 게임 결과 조회 최적화
CREATE INDEX idx_game_logs_room_started ON game_logs(room_id, started_at DESC);

-- 단어 검색 최적화
CREATE INDEX idx_word_entries_word ON word_chain_entries(word) WHERE is_valid = true;
```

### 복합 인덱스

```sql
-- 사용자별 게임 기록 조회
CREATE INDEX idx_player_stats_player_date ON player_game_stats(player_id, game_log_id);

-- 방별 시간순 단어 조회
CREATE INDEX idx_word_entries_game_round ON word_chain_entries(game_log_id, round_number, submitted_at);
```

## 데이터 무결성

### 외래키 제약조건

```sql
ALTER TABLE gamerooms 
ADD CONSTRAINT fk_gamerooms_creator 
FOREIGN KEY (created_by) REFERENCES guests(guest_id);

ALTER TABLE gameroom_participants 
ADD CONSTRAINT fk_participants_room 
FOREIGN KEY (room_id) REFERENCES gamerooms(room_id);

ALTER TABLE game_logs 
ADD CONSTRAINT fk_game_logs_winner 
FOREIGN KEY (winner_id) REFERENCES guests(guest_id);
```

### 체크 제약조건

```sql
ALTER TABLE gamerooms 
ADD CONSTRAINT chk_max_players 
CHECK (max_players > 0 AND max_players <= 20);

ALTER TABLE gamerooms 
ADD CONSTRAINT chk_time_limit 
CHECK (time_limit > 0);

ALTER TABLE player_game_stats 
ADD CONSTRAINT chk_valid_words 
CHECK (valid_words >= 0 AND invalid_words >= 0);
```

## 백업 및 복구

### 백업 스크립트

```bash
#!/bin/bash
# backup_database.sh

BACKUP_DIR="/backup/kkua"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="kkua_backup_${DATE}.sql"

# 풀 백업
pg_dump -h localhost -U postgres -d mydb > "${BACKUP_DIR}/${BACKUP_FILE}"

# 압축
gzip "${BACKUP_DIR}/${BACKUP_FILE}"

# 7일 이상 된 백업 삭제
find ${BACKUP_DIR} -name "kkua_backup_*.sql.gz" -mtime +7 -delete
```

### 복구 스크립트

```bash
#!/bin/bash
# restore_database.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# 압축 해제
gunzip -k "$BACKUP_FILE"
UNZIPPED_FILE="${BACKUP_FILE%.*}"

# 데이터베이스 복구
psql -h localhost -U postgres -d mydb < "$UNZIPPED_FILE"

# 임시 파일 삭제
rm "$UNZIPPED_FILE"
```

## 마이그레이션

### Alembic 설정

```python
# alembic/env.py
from models.gameroom_model import *
from models.guest_model import *
from models.game_log_model import *

target_metadata = Base.metadata
```

### 마이그레이션 생성

```bash
# 마이그레이션 파일 생성
alembic revision --autogenerate -m "Add game result tracking"

# 마이그레이션 실행
alembic upgrade head

# 롤백
alembic downgrade -1
```

이 데이터베이스 스키마는 현재 요구사항을 충족하면서도 향후 기능 확장을 고려한 설계입니다.