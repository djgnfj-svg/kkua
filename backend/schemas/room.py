from pydantic import BaseModel
from typing import Optional

# API 응답 모델
class RoomOut(BaseModel):
    id: int
    title: str
    people: int
    room_type: str
    max_people: int
    playing: bool
    
    class Config:
        orm_mode = True

# API 요청 모델
class RoomCreate(BaseModel):
    title: str
    room_type: str
    max_people: int = 4

class RoomUpdate(BaseModel):
    title: Optional[str] = None 