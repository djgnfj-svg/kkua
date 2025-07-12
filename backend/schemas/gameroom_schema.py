from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
import datetime


class GameStatus(str, Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"


# 게임룸 기본 모델
class GameroomBase(BaseModel):
    title: str
    max_players: int = 8
    game_mode: str = "standard"
    time_limit: int = 300
    max_rounds: int = 10
    room_type: str = "normal"


# 게임룸 생성 요청 스키마
class CreateGameroomRequest(GameroomBase):
    pass


# 게임룸 업데이트 요청 스키마
class GameroomUpdate(BaseModel):
    title: Optional[str] = None
    max_players: Optional[int] = None
    game_mode: Optional[str] = None
    time_limit: Optional[int] = None
    max_rounds: Optional[int] = None
    room_type: Optional[str] = None


# 게임룸 응답 스키마
class GameroomResponse(GameroomBase):
    room_id: int
    created_by: int
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    participant_count: int = 0

    class Config:
        orm_mode = True
        from_attributes = True


# 게임룸 목록 응답 스키마
class GameroomListResponse(BaseModel):
    rooms: List[GameroomResponse]
    total: int

    class Config:
        orm_mode = True


class GameroomCreate(GameroomBase):
    created_by: int


# 게임 결과 관련 스키마
class PlayerGameResult(BaseModel):
    guest_id: int
    nickname: str
    words_submitted: int = 0
    total_score: int = 0
    avg_response_time: float = 0.0
    longest_word: str = ""
    rank: int = 1


class WordChainEntry(BaseModel):
    word: str
    player_id: int
    player_name: str
    timestamp: datetime.datetime
    response_time: Optional[float] = None


class GameResultResponse(BaseModel):
    room_id: int
    winner_id: Optional[int] = None
    winner_name: Optional[str] = None
    players: List[PlayerGameResult]
    used_words: List[WordChainEntry]
    total_rounds: int
    game_duration: str
    total_words: int
    average_response_time: float
    longest_word: str
    fastest_response: float
    slowest_response: float
    mvp_id: Optional[int] = None
    mvp_name: Optional[str] = None
    started_at: Optional[datetime.datetime] = None
    ended_at: Optional[datetime.datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True
