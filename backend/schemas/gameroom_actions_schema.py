from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from enum import Enum
import datetime

from schemas.gameroom_schema import GameroomBase

# 게임룸 참가 응답 스키마
class JoinGameroomResponse(BaseModel):
    room_id: int
    guest_id: int
    message: str

# 게임룸 상세 응답 스키마
class GameroomDetailResponse(BaseModel):
    room_id: int
    title: str
    max_players: int
    game_mode: str
    created_by: int
    created_username: Optional[str] = None
    status: str
    participants: List[Dict[str, Any]]
    time_limit: int = 120
    
    class Config:
        from_attributes = True
        orm_mode = True

class ParticipantBase(BaseModel):
    guest_id: int
    status: str

class ParticipantInfo(ParticipantBase):
    id: int
    nickname: str
    is_creator: bool
    joined_at: datetime.datetime

    class Config:
        from_attributes = True

class GameroomParticipantsList(BaseModel):
    participants: List[ParticipantInfo] 