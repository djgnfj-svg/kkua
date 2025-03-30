from pydantic import BaseModel
import datetime

class GameresultBase(BaseModel):
    room_id: int
    guest_id: int
    score: int
    rank: int

class GameresultCreate(GameresultBase):
    pass

class GameresultResponse(GameresultBase):
    result_id: int
    played_at: datetime.datetime

    class Config:
        orm_mode = True 