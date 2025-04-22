from pydantic import BaseModel
import datetime

class WebSocketMessage(BaseModel):
    type: str
    data: dict
    
class ChatMessage(BaseModel):
    guest_id: int
    nickname: str
    message: str
    timestamp: datetime.datetime 