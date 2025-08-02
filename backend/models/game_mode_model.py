"""
게임 모드 관련 데이터 모델
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from db.postgres import Base


class GameMode(Base):
    """게임 모드 정의"""
    __tablename__ = "game_modes"
    
    mode_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(String(500))
    
    # 게임 설정
    turn_time_limit = Column(Integer, default=30)  # 턴 제한 시간 (초)
    max_rounds = Column(Integer, default=10)       # 최대 라운드
    min_word_length = Column(Integer, default=2)   # 최소 단어 길이
    max_word_length = Column(Integer, default=10)  # 최대 단어 길이
    
    # 점수 설정
    score_multiplier = Column(Float, default=1.0)  # 점수 배수
    enable_advanced_scoring = Column(Boolean, default=True)  # 고급 점수 시스템 사용
    
    # 특수 규칙
    special_rules = Column(JSON, default=dict)  # 특수 규칙 JSON
    
    # 상태
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # 메타데이터
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    

# 기본 게임 모드 설정
DEFAULT_GAME_MODES = [
    {
        "name": "classic",
        "display_name": "클래식 모드",
        "description": "기본적인 끝말잇기 게임입니다.",
        "turn_time_limit": 30,
        "max_rounds": 10,
        "min_word_length": 2,
        "max_word_length": 10,
        "score_multiplier": 1.0,
        "enable_advanced_scoring": True,
        "special_rules": {},
        "is_default": True,
        "is_active": True
    },
    {
        "name": "blitz",
        "display_name": "블리츠 모드",
        "description": "빠른 속도의 짧은 게임! 턴당 10초, 모든 점수 1.5배!",
        "turn_time_limit": 10,
        "max_rounds": 5,
        "min_word_length": 2,
        "max_word_length": 10,
        "score_multiplier": 1.5,
        "enable_advanced_scoring": True,
        "special_rules": {
            "fast_paced": True,
            "bonus_description": "빠른 게임으로 모든 점수 1.5배!"
        },
        "is_default": False,
        "is_active": True
    },
    {
        "name": "marathon",
        "display_name": "마라톤 모드",
        "description": "긴 시간 지속되는 게임! 5글자 이상 단어만 허용됩니다.",
        "turn_time_limit": 45,
        "max_rounds": 20,
        "min_word_length": 5,
        "max_word_length": 10,
        "score_multiplier": 1.2,
        "enable_advanced_scoring": True,
        "special_rules": {
            "long_words_only": True,
            "extended_time": True,
            "bonus_description": "긴 단어만 사용하여 더 높은 점수 획득!"
        },
        "is_default": False,
        "is_active": True
    },
    {
        "name": "speed",
        "display_name": "스피드 모드",
        "description": "초고속 게임! 턴당 5초, 연속 성공 시 추가 보너스!",
        "turn_time_limit": 5,
        "max_rounds": 8,
        "min_word_length": 2,
        "max_word_length": 8,
        "score_multiplier": 2.0,
        "enable_advanced_scoring": True,
        "special_rules": {
            "ultra_fast": True,
            "combo_bonus_multiplier": 1.5,
            "bonus_description": "초고속 게임으로 콤보 보너스 1.5배 추가!"
        },
        "is_default": False,
        "is_active": True
    }
]