from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Item(Base):
    """아이템 모델"""
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    rarity = Column(String(20), nullable=False, index=True)  # common, uncommon, rare, epic, legendary
    effect_type = Column(String(30), nullable=False, index=True)  # timer_extend, score_multiply, word_hint 등
    effect_value = Column(JSON)  # 아이템 효과 값
    cooldown_seconds = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    user_items = relationship("UserItem", back_populates="item")
    
    def __repr__(self):
        return f"<Item(name='{self.name}', rarity='{self.rarity}', effect_type='{self.effect_type}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "rarity": self.rarity,
            "effect_type": self.effect_type,
            "effect_value": self.effect_value,
            "cooldown_seconds": self.cooldown_seconds,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def get_rarity_color(cls, rarity: str) -> str:
        """희귀도별 색상 반환"""
        colors = {
            "common": "#9CA3AF",      # 회색
            "uncommon": "#10B981",    # 초록색
            "rare": "#3B82F6",       # 파란색
            "epic": "#8B5CF6",       # 보라색
            "legendary": "#F59E0B"   # 주황색
        }
        return colors.get(rarity, "#9CA3AF")
    
    @classmethod
    def get_rarity_drop_rate(cls, rarity: str) -> float:
        """희귀도별 드롭 확률 반환"""
        rates = {
            "common": 0.60,      # 60%
            "uncommon": 0.25,    # 25%
            "rare": 0.10,        # 10%
            "epic": 0.04,        # 4%
            "legendary": 0.01    # 1%
        }
        return rates.get(rarity, 0.0)
    
    def can_use(self, last_used_at: DateTime = None) -> bool:
        """쿨다운 시간 체크"""
        if not last_used_at:
            return True
        
        if self.cooldown_seconds == 0:
            return True
            
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        time_diff = (now - last_used_at).total_seconds()
        
        return time_diff >= self.cooldown_seconds