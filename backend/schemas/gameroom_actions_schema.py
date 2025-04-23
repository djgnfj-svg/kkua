from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from enum import Enum
import datetime

from schemas.gameroom_schema import GameroomBase, GameroomResponse

class ParticipantBase(BaseModel):
    guest_id: int
    room_id: int
    status: str

class ParticipantInfo(BaseModel):
    guest_id: int
    nickname: str
    is_creator: bool
    joined_at: datetime.datetime
    status: Optional[str] = "waiting"

    class Config:
        from_attributes = True

# 게임룸 상세 응답 스키마
class GameroomDetailResponse(BaseModel):
    room: GameroomResponse
    participants: List[ParticipantInfo]

    class Config:
        from_attributes = True

# 게임룸 참가 응답 스키마
class JoinGameroomResponse(BaseModel):
    room_id: int
    guest_id: int
    message: str

class GameroomParticipantsList(BaseModel):
    participants: List[ParticipantInfo] 