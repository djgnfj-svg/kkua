from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from db.postgres import Base


class Item(Base):
    """게임 아이템 모델"""
    __tablename__ = "items"
    
    item_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    effect_type = Column(String(30), nullable=False)  # skip_turn, extra_time, score_boost
    effect_value = Column(Integer, default=0)  # 효과 강도/지속시간
    cost = Column(Integer, default=10)  # 구매 비용 (점수)
    cooldown_seconds = Column(Integer, default=60)  # 재사용 대기시간
    rarity = Column(String(20), default="common")  # common, rare, epic
    is_active = Column(Boolean, default=True)  # 활성화 여부
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PlayerInventory(Base):
    """플레이어 아이템 인벤토리"""
    __tablename__ = "player_inventories"
    
    inventory_id = Column(Integer, primary_key=True, index=True)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.item_id"), nullable=False)
    quantity = Column(Integer, default=1)
    acquired_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    item = relationship("Item")


class ItemUsageLog(Base):
    """아이템 사용 기록"""
    __tablename__ = "item_usage_logs"
    
    usage_id = Column(Integer, primary_key=True, index=True)
    game_room_id = Column(Integer, nullable=False)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.item_id"), nullable=False)
    target_guest_id = Column(Integer, ForeignKey("guests.guest_id"))  # 대상이 있는 아이템
    used_at = Column(DateTime, default=datetime.utcnow)
    effect_applied = Column(Boolean, default=True)
    game_round = Column(Integer, default=1)
    
    # 관계 설정
    item = relationship("Item")


# 기본 아이템 데이터 정의
DEFAULT_ITEMS = [
    {
        "name": "턴 스킵",
        "description": "상대방의 턴을 건너뛰고 바로 내 턴으로 만듭니다",
        "effect_type": "skip_turn",
        "effect_value": 1,
        "cost": 15,
        "cooldown_seconds": 60,
        "rarity": "common"
    },
    {
        "name": "시간 연장",
        "description": "현재 턴의 제한 시간을 15초 추가합니다",
        "effect_type": "extra_time",
        "effect_value": 15,
        "cost": 10,
        "cooldown_seconds": 45,
        "rarity": "common"
    },
    {
        "name": "점수 배수",
        "description": "다음 단어의 점수를 2배로 받습니다",
        "effect_type": "score_multiplier",
        "effect_value": 2,
        "cost": 20,
        "cooldown_seconds": 90,
        "rarity": "rare"
    },
    {
        "name": "단어 힌트",
        "description": "사용 가능한 단어의 첫 글자 힌트를 제공합니다",
        "effect_type": "word_hint",
        "effect_value": 1,
        "cost": 8,
        "cooldown_seconds": 30,
        "rarity": "common"
    },
    {
        "name": "보호막",
        "description": "다음 한 턴 동안 다른 플레이어의 아이템 효과를 무시합니다",
        "effect_type": "immunity",
        "effect_value": 1,
        "cost": 25,
        "cooldown_seconds": 120,
        "rarity": "rare"
    }
]