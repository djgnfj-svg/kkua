from pydantic import BaseModel
import datetime
from typing import List, Optional

class WebSocketMessage(BaseModel):
    type: str
    data: dict
    
class ChatMessage(BaseModel):
    guest_id: int
    nickname: str
    message: str
    timestamp: datetime.datetime

# 끝말잇기 게임 관련 스키마
class WordChainWord(BaseModel):
    word: str
    submitted_by: int
    nickname: str
    timestamp: datetime.datetime
    is_valid: bool = True

class WordChainGameState(BaseModel):
    current_word: str
    current_player_id: int
    current_player_nickname: str
    last_character: str
    remaining_time: int
    words_used: List[WordChainWord] = []
    turn_number: int = 1
    
class WordChainSubmission(BaseModel):
    word: str
    guest_id: int
    timestamp: datetime.datetime 