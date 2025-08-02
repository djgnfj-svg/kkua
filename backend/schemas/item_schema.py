from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ItemType(str, Enum):
    """아이템 타입 열거형"""
    SKIP_TURN = "skip_turn"
    EXTRA_TIME = "extra_time"
    SCORE_MULTIPLIER = "score_multiplier"
    WORD_HINT = "word_hint"
    IMMUNITY = "immunity"


class ItemRarity(str, Enum):
    """아이템 희귀도"""
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class ItemBase(BaseModel):
    """아이템 기본 스키마"""
    name: str
    description: str
    effect_type: ItemType
    effect_value: int = 0
    cost: int = 10
    cooldown_seconds: int = 60
    rarity: ItemRarity = ItemRarity.COMMON


class ItemResponse(ItemBase):
    """아이템 응답 스키마"""
    item_id: int
    is_active: bool = True
    created_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True


class ItemInventoryResponse(BaseModel):
    """플레이어 인벤토리 아이템 응답"""
    inventory_id: int
    item: ItemResponse
    quantity: int
    acquired_at: datetime
    
    class Config:
        orm_mode = True


class ItemUseRequest(BaseModel):
    """아이템 사용 요청"""
    item_id: int
    target_guest_id: Optional[int] = None  # 대상이 있는 아이템인 경우


class ItemUseResponse(BaseModel):
    """아이템 사용 응답"""
    success: bool
    message: str
    effect_applied: bool = False
    cooldown_remaining: Optional[int] = None
    next_available_at: Optional[datetime] = None


class ItemEffectStatus(BaseModel):
    """현재 적용 중인 아이템 효과 상태"""
    guest_id: int
    active_effects: List[dict]  # [{effect_type, remaining_time, source_item}]
    immunities: List[str]  # 무시할 수 있는 효과 타입들
    cooldowns: dict  # {item_id: remaining_seconds}


class ItemPurchaseRequest(BaseModel):
    """아이템 구매 요청"""
    item_id: int
    quantity: int = 1


class ItemPurchaseResponse(BaseModel):
    """아이템 구매 응답"""
    success: bool
    message: str
    current_score: int
    items_purchased: int
    total_cost: int


class GameItemState(BaseModel):
    """게임 중 아이템 상태"""
    guest_id: int
    available_items: List[ItemInventoryResponse]
    active_effects: List[dict]
    cooldowns: dict
    can_use_items: bool = True