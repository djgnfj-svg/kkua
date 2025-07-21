# 전략적 아이템 시스템 구현 가이드

## 🎯 아이템 시스템 개요

### 설계 목표
- **전략적 깊이 추가**: 단순한 끝말잇기를 넘어선 전술적 게임플레이
- **플레이어 간 상호작용**: 경쟁적 요소와 심리전 도입
- **게임 밸런스**: 실력 차이를 완화하면서도 스킬의 중요성 유지
- **수익화 기반**: 게임 내 화폐 시스템을 통한 지속적 참여 유도

### 아이템 카테고리
1. **공격형 아이템**: 상대방을 방해하는 효과
2. **방어형 아이템**: 자신을 보호하는 효과  
3. **보조형 아이템**: 게임플레이를 도와주는 효과
4. **특수형 아이템**: 게임 규칙을 일시적으로 변경하는 효과

---

## 🔧 데이터 모델 설계

### 아이템 정의 테이블
```python
# backend/models/item_model.py
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum
from datetime import datetime

Base = declarative_base()

class ItemType(str, Enum):
    OFFENSIVE = "offensive"    # 공격형
    DEFENSIVE = "defensive"    # 방어형
    SUPPORT = "support"        # 보조형
    SPECIAL = "special"        # 특수형

class ItemRarity(str, Enum):
    COMMON = "common"          # 흔함 (회색)
    UNCOMMON = "uncommon"      # 일반 (초록)
    RARE = "rare"             # 희귀 (파랑)
    EPIC = "epic"             # 영웅 (보라)
    LEGENDARY = "legendary"    # 전설 (주황)

class Item(Base):
    """게임 아이템 정의"""
    __tablename__ = "items"
    
    item_id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    flavor_text = Column(Text)  # 재미있는 설명 텍스트
    
    # 아이템 분류
    item_type = Column(String(20), nullable=False)  # ItemType enum
    rarity = Column(String(20), nullable=False)     # ItemRarity enum
    
    # 비용 및 제한
    purchase_cost = Column(Integer, default=0)      # 구매 비용 (게임머니)
    usage_cost = Column(Integer, default=0)         # 사용 비용 (별도)
    cooldown_seconds = Column(Integer, default=0)   # 재사용 대기시간
    max_per_game = Column(Integer, default=3)       # 게임당 최대 사용 횟수
    
    # 효과 정의 (JSON으로 저장)
    effect_config = Column(JSON, nullable=False)
    
    # 메타데이터
    is_active = Column(Boolean, default=True)       # 활성화 여부
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

class PlayerInventory(Base):
    """플레이어 아이템 인벤토리"""
    __tablename__ = "player_inventories"
    
    inventory_id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.item_id"), nullable=False)
    
    quantity = Column(Integer, default=1)
    acquired_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    
    # 복합 인덱스 (한 플레이어가 같은 아이템을 여러 개 가질 수 없음)
    __table_args__ = (UniqueConstraint('guest_id', 'item_id'),)

class GameItemUsage(Base):
    """게임 내 아이템 사용 기록"""
    __tablename__ = "game_item_usages"
    
    usage_id = Column(Integer, primary_key=True)
    game_log_id = Column(Integer, ForeignKey("game_logs.id"))
    guest_id = Column(Integer, ForeignKey("guests.guest_id"))
    item_id = Column(Integer, ForeignKey("items.item_id"))
    
    target_guest_id = Column(Integer, ForeignKey("guests.guest_id"))  # 대상 플레이어 (있는 경우)
    turn_number = Column(Integer)
    round_number = Column(Integer)
    
    effect_result = Column(JSON)  # 효과 적용 결과
    used_at = Column(DateTime, default=datetime.utcnow)

class PlayerCurrency(Base):
    """플레이어 게임 화폐"""
    __tablename__ = "player_currencies"
    
    currency_id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), unique=True)
    
    coins = Column(Integer, default=100)        # 기본 화폐 (게임 완료시 획득)
    gems = Column(Integer, default=0)           # 프리미엄 화폐 (특별 성취시 획득)
    
    # 통계
    total_earned = Column(Integer, default=0)   # 총 획득량
    total_spent = Column(Integer, default=0)    # 총 소모량
    
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

### 아이템 정의 데이터
```python
# backend/data/item_definitions.py
ITEM_DEFINITIONS = {
    # 공격형 아이템
    "skip_turn": {
        "name": "턴 스킵",
        "description": "상대방의 턴을 건너뛰고 바로 내 턴으로 만듭니다",
        "flavor_text": "\"잠깐, 내가 먼저!\"",
        "item_type": "offensive",
        "rarity": "common",
        "purchase_cost": 15,
        "cooldown_seconds": 60,
        "max_per_game": 2,
        "effect_config": {
            "type": "skip_next_player",
            "duration": 0,
            "target": "next_player"
        }
    },
    
    "steal_points": {
        "name": "점수 훔치기",
        "description": "가장 높은 점수 플레이어에게서 점수의 20%를 가져옵니다",
        "flavor_text": "\"네 것은 내 것, 내 것도 내 것\"",
        "item_type": "offensive", 
        "rarity": "epic",
        "purchase_cost": 40,
        "cooldown_seconds": 180,
        "max_per_game": 1,
        "effect_config": {
            "type": "steal_score",
            "percentage": 20,
            "target": "highest_score_player"
        }
    },
    
    "confusion_bomb": {
        "name": "혼란 폭탄",
        "description": "모든 플레이어의 턴 순서를 무작위로 섞습니다",
        "flavor_text": "\"이제 누구 턴인지 아무도 모른다!\"",
        "item_type": "offensive",
        "rarity": "rare",
        "purchase_cost": 25,
        "cooldown_seconds": 120,
        "max_per_game": 1,
        "effect_config": {
            "type": "shuffle_turn_order",
            "target": "all_players"
        }
    },
    
    # 방어형 아이템
    "shield": {
        "name": "보호막",
        "description": "다음 3턴 동안 공격형 아이템의 영향을 받지 않습니다",
        "flavor_text": "\"마법의 방패가 당신을 보호합니다\"",
        "item_type": "defensive",
        "rarity": "uncommon",
        "purchase_cost": 20,
        "cooldown_seconds": 90,
        "max_per_game": 2,
        "effect_config": {
            "type": "immunity_shield",
            "duration": 3,
            "target": "self"
        }
    },
    
    "counter_attack": {
        "name": "반격",
        "description": "공격형 아이템을 사용한 플레이어에게 같은 효과를 되돌려줍니다",
        "flavor_text": "\"되로 주고 말로 받는다\"",
        "item_type": "defensive",
        "rarity": "rare",
        "purchase_cost": 30,
        "cooldown_seconds": 150,
        "max_per_game": 1,
        "effect_config": {
            "type": "reflect_effect",
            "duration": 2,
            "target": "self"
        }
    },
    
    # 보조형 아이템
    "extra_time": {
        "name": "시간 연장",
        "description": "현재 턴의 제한 시간을 15초 추가합니다",
        "flavor_text": "\"조금만 더 시간을...\"",
        "item_type": "support",
        "rarity": "common",
        "purchase_cost": 10,
        "cooldown_seconds": 45,
        "max_per_game": 3,
        "effect_config": {
            "type": "extend_time",
            "seconds": 15,
            "target": "current_turn"
        }
    },
    
    "word_hint": {
        "name": "단어 힌트",
        "description": "사용 가능한 단어의 첫 글자 힌트를 3개 제공합니다",
        "flavor_text": "\"힌트: ㄱ, ㄴ, ㄷ...\"",
        "item_type": "support",
        "rarity": "common",
        "purchase_cost": 8,
        "cooldown_seconds": 30,
        "max_per_game": 3,
        "effect_config": {
            "type": "show_hints",
            "hint_count": 3,
            "target": "self"
        }
    },
    
    "score_boost": {
        "name": "점수 부스터",
        "description": "다음 단어의 점수를 2배로 받습니다",
        "flavor_text": "\"더블 업!\"",
        "item_type": "support",
        "rarity": "uncommon",
        "purchase_cost": 18,
        "cooldown_seconds": 75,
        "max_per_game": 2,
        "effect_config": {
            "type": "score_multiplier",
            "multiplier": 2.0,
            "duration": 1,
            "target": "self"
        }
    },
    
    "inspiration": {
        "name": "영감",
        "description": "희귀한 단어 사용 시 보너스 점수가 2배가 됩니다 (3턴)",
        "flavor_text": "\"창의력이 폭발한다!\"",
        "item_type": "support",
        "rarity": "rare",
        "purchase_cost": 28,
        "cooldown_seconds": 100,
        "max_per_game": 1,
        "effect_config": {
            "type": "rarity_bonus_boost",
            "multiplier": 2.0,
            "duration": 3,
            "target": "self"
        }
    },
    
    # 특수형 아이템
    "time_freeze": {
        "name": "시간 정지",
        "description": "모든 플레이어의 턴 타이머를 3턴 동안 무제한으로 만듭니다",
        "flavor_text": "\"시간이여, 멈춰라!\"",
        "item_type": "special",
        "rarity": "epic",
        "purchase_cost": 35,
        "cooldown_seconds": 200,
        "max_per_game": 1,
        "effect_config": {
            "type": "disable_timers",
            "duration": 3,
            "target": "all_players"
        }
    },
    
    "word_bank": {
        "name": "단어 은행",
        "description": "이미 사용된 단어를 다시 사용할 수 있게 합니다 (1회)",
        "flavor_text": "\"재활용의 힘!\"",
        "item_type": "special",
        "rarity": "legendary",
        "purchase_cost": 50,
        "cooldown_seconds": 300,
        "max_per_game": 1,
        "effect_config": {
            "type": "reuse_word",
            "uses": 1,
            "target": "self"
        }
    },
    
    "golden_word": {
        "name": "황금 단어",
        "description": "다음 단어가 무조건 성공하며 3배 점수를 받습니다",
        "flavor_text": "\"완벽한 한 수!\"",
        "item_type": "special",
        "rarity": "legendary",
        "purchase_cost": 60,
        "cooldown_seconds": 999,  # 게임당 1회만
        "max_per_game": 1,
        "effect_config": {
            "type": "guaranteed_success",
            "score_multiplier": 3.0,
            "target": "self"
        }
    }
}
```

---

## 🎮 아이템 시스템 서비스 구현

### 아이템 관리 서비스
```python
# backend/services/item_service.py
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from models.item_model import Item, PlayerInventory, GameItemUsage, PlayerCurrency
from models.guest_model import Guest
from data.item_definitions import ITEM_DEFINITIONS
import json

class ItemService:
    def __init__(self, db: Session):
        self.db = db
    
    async def initialize_items(self):
        """아이템 정의를 데이터베이스에 초기화"""
        for item_key, item_data in ITEM_DEFINITIONS.items():
            existing_item = self.db.query(Item).filter(Item.name == item_data["name"]).first()
            if not existing_item:
                new_item = Item(
                    name=item_data["name"],
                    description=item_data["description"],
                    flavor_text=item_data.get("flavor_text", ""),
                    item_type=item_data["item_type"],
                    rarity=item_data["rarity"],
                    purchase_cost=item_data["purchase_cost"],
                    cooldown_seconds=item_data["cooldown_seconds"],
                    max_per_game=item_data["max_per_game"],
                    effect_config=item_data["effect_config"]
                )
                self.db.add(new_item)
        
        self.db.commit()
    
    async def get_shop_items(self, guest_id: int) -> List[Dict[str, Any]]:
        """아이템 상점 목록 조회"""
        # 플레이어 화폐 조회
        currency = await self.get_player_currency(guest_id)
        
        # 모든 활성 아이템 조회
        items = self.db.query(Item).filter(Item.is_active == True).all()
        
        shop_items = []
        for item in items:
            # 플레이어가 이미 소유하고 있는지 확인
            owned = self.db.query(PlayerInventory).filter(
                PlayerInventory.guest_id == guest_id,
                PlayerInventory.item_id == item.item_id
            ).first()
            
            shop_items.append({
                "item_id": item.item_id,
                "name": item.name,
                "description": item.description,
                "flavor_text": item.flavor_text,
                "item_type": item.item_type,
                "rarity": item.rarity,
                "purchase_cost": item.purchase_cost,
                "owned": owned is not None,
                "can_afford": currency["coins"] >= item.purchase_cost
            })
        
        return shop_items
    
    async def purchase_item(self, guest_id: int, item_id: int) -> Dict[str, Any]:
        """아이템 구매"""
        # 아이템 정보 조회
        item = self.db.query(Item).filter(Item.item_id == item_id).first()
        if not item:
            return {"success": False, "error": "아이템을 찾을 수 없습니다"}
        
        # 이미 소유하고 있는지 확인
        existing = self.db.query(PlayerInventory).filter(
            PlayerInventory.guest_id == guest_id,
            PlayerInventory.item_id == item_id
        ).first()
        if existing:
            return {"success": False, "error": "이미 소유하고 있는 아이템입니다"}
        
        # 플레이어 화폐 확인
        currency = await self.get_player_currency(guest_id)
        if currency["coins"] < item.purchase_cost:
            return {"success": False, "error": "코인이 부족합니다"}
        
        # 화폐 차감
        await self.update_player_currency(guest_id, coins_change=-item.purchase_cost)
        
        # 인벤토리에 추가
        inventory_item = PlayerInventory(
            guest_id=guest_id,
            item_id=item_id
        )
        self.db.add(inventory_item)
        self.db.commit()
        
        return {
            "success": True,
            "item_name": item.name,
            "remaining_coins": currency["coins"] - item.purchase_cost
        }
    
    async def get_player_inventory(self, guest_id: int) -> List[Dict[str, Any]]:
        """플레이어 인벤토리 조회"""
        inventory_query = self.db.query(PlayerInventory, Item).join(
            Item, PlayerInventory.item_id == Item.item_id
        ).filter(PlayerInventory.guest_id == guest_id)
        
        inventory = []
        for inv_item, item in inventory_query.all():
            inventory.append({
                "inventory_id": inv_item.inventory_id,
                "item_id": item.item_id,
                "name": item.name,
                "description": item.description,
                "item_type": item.item_type,
                "rarity": item.rarity,
                "effect_config": item.effect_config,
                "cooldown_seconds": item.cooldown_seconds,
                "max_per_game": item.max_per_game,
                "acquired_at": inv_item.acquired_at,
                "last_used": inv_item.last_used
            })
        
        return inventory
    
    async def get_player_currency(self, guest_id: int) -> Dict[str, int]:
        """플레이어 화폐 조회"""
        currency = self.db.query(PlayerCurrency).filter(
            PlayerCurrency.guest_id == guest_id
        ).first()
        
        if not currency:
            # 새 플레이어인 경우 기본 화폐 생성
            currency = PlayerCurrency(guest_id=guest_id, coins=100, gems=0)
            self.db.add(currency)
            self.db.commit()
        
        return {
            "coins": currency.coins,
            "gems": currency.gems,
            "total_earned": currency.total_earned,
            "total_spent": currency.total_spent
        }
    
    async def update_player_currency(self, guest_id: int, coins_change: int = 0, gems_change: int = 0):
        """플레이어 화폐 업데이트"""
        currency = self.db.query(PlayerCurrency).filter(
            PlayerCurrency.guest_id == guest_id
        ).first()
        
        if not currency:
            currency = PlayerCurrency(guest_id=guest_id)
            self.db.add(currency)
        
        currency.coins = max(0, currency.coins + coins_change)
        currency.gems = max(0, currency.gems + gems_change)
        
        # 통계 업데이트
        if coins_change > 0:
            currency.total_earned += coins_change
        elif coins_change < 0:
            currency.total_spent += abs(coins_change)
        
        self.db.commit()
    
    async def can_use_item_in_game(self, guest_id: int, item_id: int, game_log_id: int) -> Dict[str, Any]:
        """게임 내 아이템 사용 가능 여부 확인"""
        # 인벤토리에 아이템이 있는지 확인
        inventory_item = self.db.query(PlayerInventory).filter(
            PlayerInventory.guest_id == guest_id,
            PlayerInventory.item_id == item_id
        ).first()
        
        if not inventory_item:
            return {"can_use": False, "reason": "아이템을 소유하고 있지 않습니다"}
        
        # 아이템 정보 조회
        item = self.db.query(Item).filter(Item.item_id == item_id).first()
        
        # 게임 내 사용 횟수 확인
        usage_count = self.db.query(GameItemUsage).filter(
            GameItemUsage.game_log_id == game_log_id,
            GameItemUsage.guest_id == guest_id,
            GameItemUsage.item_id == item_id
        ).count()
        
        if usage_count >= item.max_per_game:
            return {"can_use": False, "reason": f"게임당 최대 {item.max_per_game}회까지 사용할 수 있습니다"}
        
        # 쿨다운 확인
        if inventory_item.last_used:
            time_since_use = (datetime.utcnow() - inventory_item.last_used).total_seconds()
            if time_since_use < item.cooldown_seconds:
                remaining_cooldown = item.cooldown_seconds - time_since_use
                return {
                    "can_use": False, 
                    "reason": f"아직 {remaining_cooldown:.0f}초 후에 사용할 수 있습니다"
                }
        
        return {"can_use": True}
    
    async def use_item_in_game(self, guest_id: int, item_id: int, game_log_id: int, 
                              target_guest_id: Optional[int] = None) -> Dict[str, Any]:
        """게임 내 아이템 사용"""
        # 사용 가능 여부 확인
        can_use_result = await self.can_use_item_in_game(guest_id, item_id, game_log_id)
        if not can_use_result["can_use"]:
            return {"success": False, "error": can_use_result["reason"]}
        
        # 아이템 정보 조회
        item = self.db.query(Item).filter(Item.item_id == item_id).first()
        inventory_item = self.db.query(PlayerInventory).filter(
            PlayerInventory.guest_id == guest_id,
            PlayerInventory.item_id == item_id
        ).first()
        
        # 사용 기록 추가
        usage_record = GameItemUsage(
            game_log_id=game_log_id,
            guest_id=guest_id,
            item_id=item_id,
            target_guest_id=target_guest_id
        )
        self.db.add(usage_record)
        
        # 마지막 사용 시간 업데이트
        inventory_item.last_used = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "success": True,
            "item_name": item.name,
            "effect_config": item.effect_config,
            "usage_id": usage_record.usage_id
        }
```

### 게임 내 아이템 효과 처리 시스템
```python
# backend/services/item_effect_service.py
from typing import Dict, List, Any, Optional
import random
from datetime import datetime, timedelta

class ItemEffectService:
    def __init__(self, redis_client, db_session):
        self.redis = redis_client
        self.db = db_session
        self.active_effects = {}  # 게임별 활성 효과 저장
    
    async def apply_item_effect(self, room_id: int, user_id: int, item_effect: Dict, 
                               target_user_id: Optional[int] = None) -> Dict[str, Any]:
        """아이템 효과 적용"""
        effect_type = item_effect.get("type")
        
        effect_handlers = {
            "skip_next_player": self._handle_skip_turn,
            "steal_score": self._handle_steal_points,
            "shuffle_turn_order": self._handle_shuffle_order,
            "immunity_shield": self._handle_immunity_shield,
            "reflect_effect": self._handle_counter_attack,
            "extend_time": self._handle_extend_time,
            "show_hints": self._handle_word_hints,
            "score_multiplier": self._handle_score_boost,
            "rarity_bonus_boost": self._handle_inspiration,
            "disable_timers": self._handle_time_freeze,
            "reuse_word": self._handle_word_bank,
            "guaranteed_success": self._handle_golden_word
        }
        
        handler = effect_handlers.get(effect_type)
        if not handler:
            return {"success": False, "error": f"알 수 없는 효과: {effect_type}"}
        
        try:
            result = await handler(room_id, user_id, item_effect, target_user_id)
            
            # 효과 적용 성공 시 게임 상태에 기록
            if result.get("success"):
                await self._record_active_effect(room_id, user_id, item_effect, result)
            
            return result
        except Exception as e:
            return {"success": False, "error": f"효과 적용 실패: {str(e)}"}
    
    async def _handle_skip_turn(self, room_id: int, user_id: int, effect: Dict, target_id: Optional[int]) -> Dict:
        """턴 스킵 효과"""
        game_state = await self.redis.get(f"game:{room_id}")
        if not game_state:
            return {"success": False, "error": "게임 상태를 찾을 수 없습니다"}
        
        game_data = json.loads(game_state)
        participants = game_data.get("participants", [])
        current_turn_index = game_data.get("current_turn_index", 0)
        
        # 다음 플레이어 턴을 건너뛰기
        next_turn_index = (current_turn_index + 1) % len(participants)
        skipped_player = participants[next_turn_index]
        
        # 그 다음 플레이어로 턴 이동
        new_turn_index = (next_turn_index + 1) % len(participants)
        game_data["current_turn_index"] = new_turn_index
        game_data["current_player_id"] = participants[new_turn_index]["guest_id"]
        
        # 게임 상태 업데이트
        await self.redis.set(f"game:{room_id}", json.dumps(game_data))
        
        return {
            "success": True,
            "effect": "turn_skipped",
            "skipped_player": skipped_player["nickname"],
            "next_player": participants[new_turn_index]["nickname"],
            "message": f"{skipped_player['nickname']}님의 턴이 건너뛰어졌습니다!"
        }
    
    async def _handle_steal_points(self, room_id: int, user_id: int, effect: Dict, target_id: Optional[int]) -> Dict:
        """점수 훔치기 효과"""
        percentage = effect.get("percentage", 20)
        
        # 모든 플레이어 점수 조회
        player_stats = await self._get_all_player_stats(room_id)
        if not player_stats:
            return {"success": False, "error": "플레이어 통계를 찾을 수 없습니다"}
        
        # 가장 높은 점수 플레이어 찾기 (자신 제외)
        highest_score = 0
        target_player = None
        for guest_id, stats in player_stats.items():
            if guest_id != str(user_id) and stats.get("score", 0) > highest_score:
                highest_score = stats["score"]
                target_player = guest_id
        
        if not target_player or highest_score <= 0:
            return {"success": False, "error": "훔칠 점수가 있는 플레이어가 없습니다"}
        
        # 점수 계산 및 이동
        stolen_points = int(highest_score * percentage / 100)
        
        # 점수 업데이트
        player_stats[target_player]["score"] -= stolen_points
        player_stats[str(user_id)]["score"] = player_stats.get(str(user_id), {}).get("score", 0) + stolen_points
        
        # Redis 업데이트
        await self._update_all_player_stats(room_id, player_stats)
        
        return {
            "success": True,
            "effect": "points_stolen",
            "stolen_points": stolen_points,
            "from_player": target_player,
            "message": f"{stolen_points}점을 훔쳐왔습니다!"
        }
    
    async def _handle_extend_time(self, room_id: int, user_id: int, effect: Dict, target_id: Optional[int]) -> Dict:
        """시간 연장 효과"""
        extra_seconds = effect.get("seconds", 15)
        
        # 현재 턴 시간 연장
        game_state_key = f"game:{room_id}"
        game_state = await self.redis.get(game_state_key)
        if not game_state:
            return {"success": False, "error": "게임 상태를 찾을 수 없습니다"}
        
        game_data = json.loads(game_state)
        current_time_limit = game_data.get("turn_time_limit", 30)
        game_data["turn_time_limit"] = current_time_limit + extra_seconds
        
        # 현재 턴 시작 시간을 조정하여 효과적으로 시간 연장
        if game_data.get("turn_start_time"):
            game_data["turn_start_time"] -= extra_seconds
        
        await self.redis.set(game_state_key, json.dumps(game_data))
        
        return {
            "success": True,
            "effect": "time_extended",
            "extra_seconds": extra_seconds,
            "message": f"{extra_seconds}초 시간이 연장되었습니다!"
        }
    
    async def _handle_word_hints(self, room_id: int, user_id: int, effect: Dict, target_id: Optional[int]) -> Dict:
        """단어 힌트 효과"""
        hint_count = effect.get("hint_count", 3)
        
        # 현재 마지막 글자 조회
        game_state = await self.redis.get(f"game:{room_id}")
        if not game_state:
            return {"success": False, "error": "게임 상태를 찾을 수 없습니다"}
        
        game_data = json.loads(game_state)
        last_character = game_data.get("last_character", "")
        
        if not last_character:
            return {"success": False, "error": "아직 시작할 글자가 없습니다"}
        
        # 힌트 생성 (실제로는 한국어 사전 API 연동 필요)
        hints = self._generate_word_hints(last_character, hint_count)
        
        return {
            "success": True,
            "effect": "hints_provided",
            "hints": hints,
            "last_character": last_character,
            "message": f"'{last_character}'로 시작하는 단어 힌트입니다!"
        }
    
    async def _handle_score_boost(self, room_id: int, user_id: int, effect: Dict, target_id: Optional[int]) -> Dict:
        """점수 부스터 효과"""
        multiplier = effect.get("multiplier", 2.0)
        duration = effect.get("duration", 1)
        
        # 플레이어에게 점수 배수 효과 부여
        effect_key = f"game:{room_id}:effects:{user_id}:score_boost"
        effect_data = {
            "multiplier": multiplier,
            "remaining_uses": duration,
            "applied_at": datetime.utcnow().isoformat()
        }
        
        await self.redis.setex(effect_key, 600, json.dumps(effect_data))  # 10분 후 만료
        
        return {
            "success": True,
            "effect": "score_boost_applied",
            "multiplier": multiplier,
            "duration": duration,
            "message": f"다음 {duration}개 단어의 점수가 {multiplier}배가 됩니다!"
        }
    
    async def _handle_immunity_shield(self, room_id: int, user_id: int, effect: Dict, target_id: Optional[int]) -> Dict:
        """보호막 효과"""
        duration = effect.get("duration", 3)
        
        # 보호막 효과 적용
        shield_key = f"game:{room_id}:effects:{user_id}:immunity_shield"
        shield_data = {
            "remaining_turns": duration,
            "applied_at": datetime.utcnow().isoformat()
        }
        
        await self.redis.setex(shield_key, 600, json.dumps(shield_data))
        
        return {
            "success": True,
            "effect": "immunity_shield_applied",
            "duration": duration,
            "message": f"{duration}턴 동안 공격형 아이템으로부터 보호됩니다!"
        }
    
    def _generate_word_hints(self, last_character: str, count: int) -> List[str]:
        """단어 힌트 생성 (실제로는 사전 API 연동 필요)"""
        # 임시 힌트 데이터 (실제로는 한국어 사전에서 조회)
        sample_hints = {
            "가": ["가방", "가족", "가을", "가게", "가치"],
            "나": ["나무", "나라", "나비", "나이", "나침반"],
            "다": ["다리", "다음", "다양", "다른", "다시"],
            "라": ["라디오", "라면", "라이브", "라운드", "라벨"],
            "마": ["마음", "마지막", "마법", "마당", "마시다"],
            # ... 더 많은 데이터 필요
        }
        
        hints = sample_hints.get(last_character, ["단어1", "단어2", "단어3"])
        return hints[:count]
    
    async def check_active_effects(self, room_id: int, user_id: int) -> Dict[str, Any]:
        """플레이어의 활성 효과 확인"""
        effects = {}
        
        # 각종 효과 확인
        effect_types = ["score_boost", "immunity_shield", "reflect_effect", "rarity_bonus_boost"]
        
        for effect_type in effect_types:
            effect_key = f"game:{room_id}:effects:{user_id}:{effect_type}"
            effect_data = await self.redis.get(effect_key)
            if effect_data:
                effects[effect_type] = json.loads(effect_data)
        
        return effects
    
    async def consume_effect_use(self, room_id: int, user_id: int, effect_type: str):
        """효과 사용 횟수 차감"""
        effect_key = f"game:{room_id}:effects:{user_id}:{effect_type}"
        effect_data = await self.redis.get(effect_key)
        
        if effect_data:
            data = json.loads(effect_data)
            if "remaining_uses" in data:
                data["remaining_uses"] -= 1
                if data["remaining_uses"] <= 0:
                    await self.redis.delete(effect_key)
                else:
                    await self.redis.set(effect_key, json.dumps(data))
```

### 프론트엔드 아이템 인터페이스
```javascript
// frontend/src/Pages/ItemShop/ItemShop.js
import React, { useState, useEffect } from 'react';
import { itemApi } from '../../Api/itemApi';
import ItemCard from './components/ItemCard';
import CurrencyDisplay from './components/CurrencyDisplay';

const ItemShop = () => {
    const [items, setItems] = useState([]);
    const [currency, setCurrency] = useState({ coins: 0, gems: 0 });
    const [loading, setLoading] = useState(true);
    const [selectedCategory, setSelectedCategory] = useState('all');

    useEffect(() => {
        loadShopData();
    }, []);

    const loadShopData = async () => {
        try {
            setLoading(true);
            const [shopItems, playerCurrency] = await Promise.all([
                itemApi.getShopItems(),
                itemApi.getPlayerCurrency()
            ]);
            setItems(shopItems);
            setCurrency(playerCurrency);
        } catch (error) {
            console.error('상점 데이터 로딩 실패:', error);
        } finally {
            setLoading(false);
        }
    };

    const handlePurchase = async (itemId) => {
        try {
            const result = await itemApi.purchaseItem(itemId);
            if (result.success) {
                // 구매 성공 처리
                setCurrency(prev => ({ ...prev, coins: result.remaining_coins }));
                setItems(prev => prev.map(item => 
                    item.item_id === itemId 
                        ? { ...item, owned: true, can_afford: false }
                        : item
                ));
                
                // 성공 메시지 표시
                toast.showSuccess(`${result.item_name}을(를) 구매했습니다!`);
            } else {
                toast.showError(result.error);
            }
        } catch (error) {
            toast.showError('구매 중 오류가 발생했습니다.');
        }
    };

    const filterItems = (category) => {
        if (category === 'all') return items;
        return items.filter(item => item.item_type === category);
    };

    const categories = [
        { key: 'all', name: '전체', icon: '🎯' },
        { key: 'offensive', name: '공격', icon: '⚔️' },
        { key: 'defensive', name: '방어', icon: '🛡️' },
        { key: 'support', name: '보조', icon: '✨' },
        { key: 'special', name: '특수', icon: '🌟' }
    ];

    if (loading) {
        return <div className="flex justify-center items-center h-64">로딩 중...</div>;
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-6">
            <div className="max-w-6xl mx-auto">
                {/* 헤더 */}
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-4xl font-bold text-white">🏪 아이템 상점</h1>
                    <CurrencyDisplay coins={currency.coins} gems={currency.gems} />
                </div>

                {/* 카테고리 필터 */}
                <div className="flex space-x-4 mb-8">
                    {categories.map(category => (
                        <button
                            key={category.key}
                            onClick={() => setSelectedCategory(category.key)}
                            className={`px-6 py-3 rounded-lg font-medium transition-all ${
                                selectedCategory === category.key
                                    ? 'bg-purple-500 text-white'
                                    : 'bg-white/10 text-white hover:bg-white/20'
                            }`}
                        >
                            {category.icon} {category.name}
                        </button>
                    ))}
                </div>

                {/* 아이템 그리드 */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {filterItems(selectedCategory).map(item => (
                        <ItemCard
                            key={item.item_id}
                            item={item}
                            onPurchase={handlePurchase}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ItemShop;
```

```javascript
// frontend/src/Pages/ItemShop/components/ItemCard.js
import React from 'react';

const ItemCard = ({ item, onPurchase }) => {
    const getRarityStyle = (rarity) => {
        const styles = {
            common: 'border-gray-400 bg-gray-50',
            uncommon: 'border-green-400 bg-green-50',
            rare: 'border-blue-400 bg-blue-50',
            epic: 'border-purple-400 bg-purple-50',
            legendary: 'border-yellow-400 bg-yellow-50'
        };
        return styles[rarity] || styles.common;
    };

    const getRarityText = (rarity) => {
        const texts = {
            common: '일반',
            uncommon: '고급',
            rare: '희귀',
            epic: '영웅',
            legendary: '전설'
        };
        return texts[rarity] || '일반';
    };

    const getTypeIcon = (type) => {
        const icons = {
            offensive: '⚔️',
            defensive: '🛡️',
            support: '✨',
            special: '🌟'
        };
        return icons[type] || '🎯';
    };

    return (
        <div className={`rounded-xl border-2 p-6 transition-all hover:scale-105 ${getRarityStyle(item.rarity)}`}>
            {/* 아이템 헤더 */}
            <div className="flex justify-between items-start mb-4">
                <div className="text-3xl">{getTypeIcon(item.item_type)}</div>
                <div className="text-right">
                    <div className="text-sm font-medium text-gray-600">
                        {getRarityText(item.rarity)}
                    </div>
                    <div className="text-lg font-bold text-gray-800">
                        {item.purchase_cost} 🪙
                    </div>
                </div>
            </div>

            {/* 아이템 정보 */}
            <div className="mb-4">
                <h3 className="text-xl font-bold text-gray-800 mb-2">{item.name}</h3>
                <p className="text-sm text-gray-600 mb-2">{item.description}</p>
                {item.flavor_text && (
                    <p className="text-xs italic text-gray-500">"{item.flavor_text}"</p>
                )}
            </div>

            {/* 구매 버튼 */}
            <button
                onClick={() => onPurchase(item.item_id)}
                disabled={item.owned || !item.can_afford}
                className={`w-full py-3 rounded-lg font-semibold transition-all ${
                    item.owned 
                        ? 'bg-green-500 text-white cursor-not-allowed'
                        : item.can_afford
                            ? 'bg-purple-500 text-white hover:bg-purple-600'
                            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
            >
                {item.owned ? '✅ 보유중' : item.can_afford ? '구매하기' : '코인 부족'}
            </button>
        </div>
    );
};

export default ItemCard;
```

이제 아이템 시스템의 기본 구조가 완성되었습니다. 다음에는 게임 모드 다양화 가이드를 작성하겠습니다.