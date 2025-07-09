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
