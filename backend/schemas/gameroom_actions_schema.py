from pydantic import BaseModel
from typing import Optional, List
import datetime

from schemas.gameroom_schema import GameroomResponse


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


# 레디 상태 변경 응답 스키마
class ReadyStatusResponse(BaseModel):
    status: str
    message: str
    is_ready: bool


# 게임 종료 응답 스키마
class GameEndResponse(BaseModel):
    message: str
    status: str
