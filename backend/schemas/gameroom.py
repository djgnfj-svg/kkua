from pydantic import BaseModel
from typing import Optional
import datetime

class GameroomBase(BaseModel):
    title: str
    max_players: int
    game_mode: str
    time_limit: int
    status: str

class GameroomCreate(GameroomBase):
    created_by: int

class GameroomUpdate(BaseModel):
    title: Optional[str] = None
    max_players: Optional[int] = None
    game_mode: Optional[str] = None
    time_limit: Optional[int] = None
    status: Optional[str] = None

class GameroomResponse(GameroomBase):
    room_id: int
    created_by: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True 