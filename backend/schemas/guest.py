from pydantic import BaseModel
from typing import Optional
import datetime
import uuid

class GuestBase(BaseModel):
    nickname: Optional[str] = None

class GuestCreate(GuestBase):
    pass

class GuestUpdate(BaseModel):
    nickname: Optional[str] = None

class GuestResponse(GuestBase):
    guest_id: int
    uuid: uuid.UUID
    created_at: datetime.datetime
    last_login: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True 