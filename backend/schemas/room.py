from pydantic import BaseModel
from typing import Optional
import datetime

# API 응답 모델
class RoomOut(BaseModel):
    id: int
    title: str
    people: int
    room_type: str
    max_people: int
    playing: bool
    created_by: Optional[int] = None
    created_at: datetime.datetime
    
    class Config:
        orm_mode = True

# API 요청 모델
class RoomBase(BaseModel):
    title: str
    room_type: str
    max_people: int = 4

class RoomCreate(RoomBase):
    created_by: Optional[int] = None  # Guest ID

class RoomUpdate(BaseModel):
    title: Optional[str] = None
    max_people: Optional[int] = None 