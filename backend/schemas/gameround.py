from pydantic import BaseModel
import datetime

class GameroundBase(BaseModel):
    room_id: int
    guest_id: int
    word: str

class GameroundCreate(GameroundBase):
    pass

class GameroundResponse(GameroundBase):
    round_id: int
    submitted_at: datetime.datetime

    class Config:
        orm_mode = True 