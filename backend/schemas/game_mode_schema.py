"""
게임 모드 관련 Pydantic 스키마
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class GameModeBase(BaseModel):
    """게임 모드 기본 정보"""
    name: str = Field(..., max_length=50, description="게임 모드 고유 이름")
    display_name: str = Field(..., max_length=100, description="게임 모드 표시 이름")
    description: Optional[str] = Field(None, max_length=500, description="게임 모드 설명")
    
    turn_time_limit: int = Field(30, ge=5, le=300, description="턴 제한 시간(초)")
    max_rounds: int = Field(10, ge=1, le=50, description="최대 라운드 수")
    min_word_length: int = Field(2, ge=1, le=10, description="최소 단어 길이")
    max_word_length: int = Field(10, ge=2, le=20, description="최대 단어 길이")
    
    score_multiplier: float = Field(1.0, ge=0.1, le=10.0, description="점수 배수")
    enable_advanced_scoring: bool = Field(True, description="고급 점수 시스템 사용")
    
    special_rules: Dict[str, Any] = Field(default_factory=dict, description="특수 규칙")
    
    is_active: bool = Field(True, description="활성 상태")
    is_default: bool = Field(False, description="기본 모드 여부")


class GameModeCreate(GameModeBase):
    """게임 모드 생성 스키마"""
    pass


class GameModeUpdate(BaseModel):
    """게임 모드 업데이트 스키마"""
    display_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    turn_time_limit: Optional[int] = Field(None, ge=5, le=300)
    max_rounds: Optional[int] = Field(None, ge=1, le=50)
    min_word_length: Optional[int] = Field(None, ge=1, le=10)
    max_word_length: Optional[int] = Field(None, ge=2, le=20)
    
    score_multiplier: Optional[float] = Field(None, ge=0.1, le=10.0)
    enable_advanced_scoring: Optional[bool] = None
    
    special_rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class GameModeResponse(GameModeBase):
    """게임 모드 응답 스키마"""
    mode_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GameModeListResponse(BaseModel):
    """게임 모드 목록 응답"""
    modes: List[GameModeResponse]
    total: int
    active_count: int


class GameRoomModeRequest(BaseModel):
    """게임방 모드 설정 요청"""
    mode_name: str = Field(..., description="사용할 게임 모드 이름")
    custom_settings: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="커스텀 설정 (모드 설정 오버라이드)"
    )


class GameModeValidationResponse(BaseModel):
    """게임 모드 검증 응답"""
    is_valid: bool
    mode: Optional[GameModeResponse] = None
    effective_settings: Optional[Dict[str, Any]] = None
    validation_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)