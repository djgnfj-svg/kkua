from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from enum import Enum
import datetime

class GameStatus(str, Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"

# 게임룸 생성 요청 스키마 추가
class CreateGameroomRequest(BaseModel):
    title: str = Field(default="새 게임")
    max_players: int = Field(default=2, ge=2, le=8)
    game_mode: str = Field(default="arcade")
    time_limit: int = Field(default=120, ge=60, le=600)

# 게임룸 기본 스키마
class GameroomBase(BaseModel):
    title: str
    participant_count: int
    max_players: int
    game_mode: str
    time_limit: int = 120

# 게임룸 응답 스키마
class GameroomResponse(BaseModel):
    room_id: int
    title: str
    max_players: int
    game_mode: str
    created_by: int
    created_username: Optional[str] = None
    status: str
    participant_count: int
    time_limit: int = 120
    
    class Config:
        from_attributes = True
        orm_mode = True

# 게임룸 목록 응답 스키마
class GameroomListResponse(BaseModel):
    rooms: List[GameroomResponse]
    
    class Config:
        from_attributes = True
        orm_mode = True

class GameroomCreate(GameroomBase):
    created_by: int

class GameroomUpdate(BaseModel):
    title: Optional[str] = None
    max_players: Optional[int] = None
    game_mode: Optional[str] = None
    time_limit: Optional[int] = None
    status: Optional[str] = None 