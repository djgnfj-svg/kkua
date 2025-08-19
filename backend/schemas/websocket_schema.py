from pydantic import BaseModel, field_validator, Field
from typing import Any, Dict, Optional, Union, Literal
from enum import Enum


class MessageType(str, Enum):
    """WebSocket 메시지 타입 열거형"""

    CHAT = "chat"
    GAME_ACTION = "game_action"
    WORD_CHAIN = "word_chain"
    PING = "ping"
    PONG = "pong"


class GameActionType(str, Enum):
    """게임 액션 타입 열거형"""

    TOGGLE_READY = "toggle_ready"
    START_GAME = "start_game"
    END_GAME = "end_game"


class BaseWebSocketMessage(BaseModel):
    """기본 WebSocket 메시지 스키마"""

    type: MessageType

    class Config:
        use_enum_values = True


class ChatMessage(BaseWebSocketMessage):
    """채팅 메시지 스키마"""

    type: Literal[MessageType.CHAT] = MessageType.CHAT
    message: str = Field(..., min_length=1, max_length=500)
    message_id: Optional[str] = Field(None, max_length=100)

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError("메시지는 비어있을 수 없습니다")

        # 금지된 문자 체크
        forbidden_chars = ["<", ">", '"', "'", "&"]
        if any(char in v for char in forbidden_chars):
            raise ValueError("허용되지 않는 문자가 포함되어 있습니다")

        return v.strip()


class GameActionMessage(BaseWebSocketMessage):
    """게임 액션 메시지 스키마"""

    type: Literal[MessageType.GAME_ACTION] = MessageType.GAME_ACTION
    action: GameActionType
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WordChainMessage(BaseWebSocketMessage):
    """끝말잇기 단어 메시지 스키마"""

    type: Literal[MessageType.WORD_CHAIN] = MessageType.WORD_CHAIN
    word: str = Field(..., min_length=2, max_length=20)
    timestamp: Optional[float] = None

    @field_validator("word")
    @classmethod
    def validate_word(cls, v):
        # 한글만 허용
        if not all("가" <= char <= "힣" for char in v):
            raise ValueError("한글만 입력 가능합니다")

        # 공백 제거
        v = v.strip()

        if len(v) < 2:
            raise ValueError("2글자 이상 입력해주세요")

        return v


class PingMessage(BaseWebSocketMessage):
    """Ping 메시지 스키마"""

    type: Literal[MessageType.PING] = MessageType.PING
    timestamp: Optional[float] = None


class PongMessage(BaseWebSocketMessage):
    """Pong 메시지 스키마"""

    type: Literal[MessageType.PONG] = MessageType.PONG
    timestamp: Optional[float] = None


# 메시지 타입별 스키마 매핑
MESSAGE_SCHEMAS = {
    MessageType.CHAT: ChatMessage,
    MessageType.GAME_ACTION: GameActionMessage,
    MessageType.WORD_CHAIN: WordChainMessage,
    MessageType.PING: PingMessage,
    MessageType.PONG: PongMessage,
}


def validate_websocket_message(
    message_data: Dict[str, Any],
) -> Union[ChatMessage, GameActionMessage, WordChainMessage, PingMessage, PongMessage]:
    """WebSocket 메시지 검증"""
    message_type = message_data.get("type")

    if not message_type:
        raise ValueError("메시지 타입이 필요합니다")

    if message_type not in MESSAGE_SCHEMAS:
        raise ValueError(f"지원되지 않는 메시지 타입: {message_type}")

    schema_class = MESSAGE_SCHEMAS[message_type]
    return schema_class(**message_data)
