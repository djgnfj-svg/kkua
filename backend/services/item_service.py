from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import json

from models.item_model import Item, PlayerInventory, ItemUsageLog, DEFAULT_ITEMS
from models.guest_model import Guest
from schemas.item_schema import (
    ItemResponse, ItemInventoryResponse, ItemUseRequest, ItemUseResponse,
    ItemEffectStatus, ItemPurchaseRequest, ItemPurchaseResponse,
    GameItemState, ItemType
)

logger = logging.getLogger(__name__)


class ItemService:
    """아이템 관리 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.active_effects = {}  # {room_id: {guest_id: [effects]}}
        self.cooldowns = {}  # {(guest_id, item_id): end_time}
    
    def initialize_default_items(self) -> bool:
        """기본 아이템들을 데이터베이스에 초기화"""
        try:
            existing_items = self.db.query(Item).count()
            if existing_items > 0:
                logger.info("아이템이 이미 초기화되어 있습니다")
                return True
            
            for item_data in DEFAULT_ITEMS:
                item = Item(**item_data)
                self.db.add(item)
            
            self.db.commit()
            logger.info(f"{len(DEFAULT_ITEMS)}개의 기본 아이템을 초기화했습니다")
            return True
        except Exception as e:
            logger.error(f"기본 아이템 초기화 실패: {e}")
            self.db.rollback()
            return False
    
    def get_all_items(self) -> List[ItemResponse]:
        """모든 활성 아이템 조회"""
        items = self.db.query(Item).filter(Item.is_active == True).all()
        return [ItemResponse.from_orm(item) for item in items]
    
    def get_item_by_id(self, item_id: int) -> Optional[ItemResponse]:
        """아이템 ID로 조회"""
        item = self.db.query(Item).filter(
            Item.item_id == item_id,
            Item.is_active == True
        ).first()
        return ItemResponse.from_orm(item) if item else None
    
    def get_player_inventory(self, guest_id: int) -> List[ItemInventoryResponse]:
        """플레이어의 아이템 인벤토리 조회"""
        inventory_items = (
            self.db.query(PlayerInventory)
            .join(Item)
            .filter(
                PlayerInventory.guest_id == guest_id,
                PlayerInventory.quantity > 0,
                Item.is_active == True
            )
            .all()
        )
        return [ItemInventoryResponse.from_orm(item) for item in inventory_items]
    
    def purchase_item(self, guest_id: int, request: ItemPurchaseRequest) -> ItemPurchaseResponse:
        """아이템 구매"""
        try:
            # 아이템 존재 확인
            item = self.db.query(Item).filter(
                Item.item_id == request.item_id,
                Item.is_active == True
            ).first()
            
            if not item:
                return ItemPurchaseResponse(
                    success=False,
                    message="아이템을 찾을 수 없습니다",
                    current_score=0,
                    items_purchased=0,
                    total_cost=0
                )
            
            # 게스트 조회 및 점수 확인
            guest = self.db.query(Guest).filter(Guest.guest_id == guest_id).first()
            if not guest:
                return ItemPurchaseResponse(
                    success=False,
                    message="사용자를 찾을 수 없습니다",
                    current_score=0,
                    items_purchased=0,
                    total_cost=0
                )
            
            total_cost = item.cost * request.quantity
            
            # 점수 부족 체크 (향후 점수 시스템 구현 시 활성화)
            # if guest.total_score < total_cost:
            #     return ItemPurchaseResponse(
            #         success=False,
            #         message=f"점수가 부족합니다. 필요: {total_cost}, 보유: {guest.total_score}",
            #         current_score=guest.total_score,
            #         items_purchased=0,
            #         total_cost=total_cost
            #     )
            
            # 기존 인벤토리 아이템 확인
            existing_inventory = (
                self.db.query(PlayerInventory)
                .filter(
                    PlayerInventory.guest_id == guest_id,
                    PlayerInventory.item_id == request.item_id
                )
                .first()
            )
            
            if existing_inventory:
                # 기존 아이템 수량 증가
                existing_inventory.quantity += request.quantity
            else:
                # 새로운 인벤토리 항목 생성
                new_inventory = PlayerInventory(
                    guest_id=guest_id,
                    item_id=request.item_id,
                    quantity=request.quantity
                )
                self.db.add(new_inventory)
            
            # 점수 차감 (향후 구현)
            # guest.total_score -= total_cost
            
            self.db.commit()
            
            return ItemPurchaseResponse(
                success=True,
                message=f"{item.name} {request.quantity}개를 구매했습니다",
                current_score=0,  # guest.total_score,
                items_purchased=request.quantity,
                total_cost=total_cost
            )
            
        except Exception as e:
            logger.error(f"아이템 구매 실패: {e}")
            self.db.rollback()
            return ItemPurchaseResponse(
                success=False,
                message="아이템 구매 중 오류가 발생했습니다",
                current_score=0,
                items_purchased=0,
                total_cost=0
            )
    
    def use_item(self, room_id: int, guest_id: int, request: ItemUseRequest) -> ItemUseResponse:
        """게임 중 아이템 사용"""
        try:
            # 아이템 보유 확인
            inventory_item = (
                self.db.query(PlayerInventory)
                .join(Item)
                .filter(
                    PlayerInventory.guest_id == guest_id,
                    PlayerInventory.item_id == request.item_id,
                    PlayerInventory.quantity > 0,
                    Item.is_active == True
                )
                .first()
            )
            
            if not inventory_item:
                return ItemUseResponse(
                    success=False,
                    message="아이템을 보유하고 있지 않습니다"
                )
            
            # 쿨다운 확인
            cooldown_key = (guest_id, request.item_id)
            if cooldown_key in self.cooldowns:
                remaining_time = (self.cooldowns[cooldown_key] - datetime.utcnow()).total_seconds()
                if remaining_time > 0:
                    return ItemUseResponse(
                        success=False,
                        message=f"아이템이 쿨다운 중입니다. {int(remaining_time)}초 후 사용 가능",
                        cooldown_remaining=int(remaining_time)
                    )
            
            # 면역 효과 확인 (대상이 있는 아이템인 경우)
            if request.target_guest_id and self._has_immunity(room_id, request.target_guest_id, inventory_item.item.effect_type):
                return ItemUseResponse(
                    success=False,
                    message="대상이 해당 효과에 면역 상태입니다"
                )
            
            # 아이템 효과 적용
            effect_result = self._apply_item_effect(room_id, guest_id, inventory_item.item, request.target_guest_id)
            
            if effect_result["success"]:
                # 아이템 사용량 차감
                inventory_item.quantity -= 1
                
                # 쿨다운 설정
                self.cooldowns[cooldown_key] = datetime.utcnow() + timedelta(seconds=inventory_item.item.cooldown_seconds)
                
                # 사용 기록
                usage_log = ItemUsageLog(
                    game_room_id=room_id,
                    guest_id=guest_id,
                    item_id=request.item_id,
                    target_guest_id=request.target_guest_id,
                    effect_applied=True
                )
                self.db.add(usage_log)
                self.db.commit()
                
                return ItemUseResponse(
                    success=True,
                    message=effect_result["message"],
                    effect_applied=True,
                    next_available_at=self.cooldowns[cooldown_key]
                )
            else:
                return ItemUseResponse(
                    success=False,
                    message=effect_result["message"]
                )
                
        except Exception as e:
            logger.error(f"아이템 사용 실패: {e}")
            self.db.rollback()
            return ItemUseResponse(
                success=False,
                message="아이템 사용 중 오류가 발생했습니다"
            )
    
    def _apply_item_effect(self, room_id: int, user_id: int, item: Item, target_id: Optional[int] = None) -> Dict[str, Any]:
        """아이템 효과를 실제로 적용"""
        try:
            if room_id not in self.active_effects:
                self.active_effects[room_id] = {}
            
            effect_data = {
                "effect_type": item.effect_type,
                "effect_value": item.effect_value,
                "source_item": item.name,
                "source_user": user_id,
                "applied_at": datetime.utcnow(),
                "duration": item.effect_value if item.effect_type == "extra_time" else 0
            }
            
            if item.effect_type == ItemType.SKIP_TURN:
                # 턴 스킵: 다음 플레이어의 턴을 건너뛰기
                target_user = target_id or self._get_next_player(room_id, user_id)
                if target_user not in self.active_effects[room_id]:
                    self.active_effects[room_id][target_user] = []
                self.active_effects[room_id][target_user].append(effect_data)
                return {"success": True, "message": f"다음 플레이어의 턴을 스킵했습니다"}
            
            elif item.effect_type == ItemType.EXTRA_TIME:
                # 시간 연장: 현재 플레이어에게 추가 시간
                if user_id not in self.active_effects[room_id]:
                    self.active_effects[room_id][user_id] = []
                self.active_effects[room_id][user_id].append(effect_data)
                return {"success": True, "message": f"{item.effect_value}초 추가 시간을 얻었습니다"}
            
            elif item.effect_type == ItemType.SCORE_MULTIPLIER:
                # 점수 배수: 다음 단어에 적용
                if user_id not in self.active_effects[room_id]:
                    self.active_effects[room_id][user_id] = []
                self.active_effects[room_id][user_id].append(effect_data)
                return {"success": True, "message": f"다음 단어 점수가 {item.effect_value}배가 됩니다"}
            
            elif item.effect_type == ItemType.WORD_HINT:
                # 단어 힌트: 즉시 힌트 제공
                hint = self._generate_word_hint(room_id)
                return {"success": True, "message": f"힌트: '{hint}'으로 시작하는 단어를 사용해보세요"}
            
            elif item.effect_type == ItemType.IMMUNITY:
                # 면역 효과: 다른 아이템 효과 무시
                if user_id not in self.active_effects[room_id]:
                    self.active_effects[room_id][user_id] = []
                effect_data["duration"] = 1  # 1턴 동안 지속
                self.active_effects[room_id][user_id].append(effect_data)
                return {"success": True, "message": "다음 턴 동안 다른 플레이어의 아이템 효과를 무시합니다"}
            
            else:
                return {"success": False, "message": "알 수 없는 아이템 효과입니다"}
                
        except Exception as e:
            logger.error(f"아이템 효과 적용 실패: {e}")
            return {"success": False, "message": "아이템 효과 적용 중 오류가 발생했습니다"}
    
    def get_active_effects(self, room_id: int, guest_id: int) -> List[dict]:
        """플레이어의 현재 활성 효과 조회"""
        if room_id in self.active_effects and guest_id in self.active_effects[room_id]:
            return self.active_effects[room_id][guest_id]
        return []
    
    def clear_room_effects(self, room_id: int):
        """방의 모든 효과 제거 (게임 종료 시)"""
        if room_id in self.active_effects:
            del self.active_effects[room_id]
    
    def _has_immunity(self, room_id: int, guest_id: int, effect_type: str) -> bool:
        """플레이어가 특정 효과에 면역인지 확인"""
        effects = self.get_active_effects(room_id, guest_id)
        return any(effect["effect_type"] == ItemType.IMMUNITY for effect in effects)
    
    def _get_next_player(self, room_id: int, current_player: int) -> int:
        """다음 플레이어 ID를 가져오기 (실제 구현에서는 게임 상태에서 조회)"""
        # 임시 구현 - 실제로는 Redis 게임 상태에서 가져와야 함
        return current_player + 1
    
    def _generate_word_hint(self, room_id: int) -> str:
        """단어 힌트 생성 (실제 구현에서는 게임 상태 기반)"""
        # 임시 구현 - 실제로는 현재 게임 상태와 사용 가능한 단어를 기반으로 생성
        common_hints = ["가", "나", "다", "라", "마", "바", "사", "아", "자", "차"]
        import random
        return random.choice(common_hints)
    
    def get_game_item_state(self, room_id: int, guest_id: int) -> GameItemState:
        """게임 중 플레이어의 아이템 상태 조회"""
        inventory = self.get_player_inventory(guest_id)
        active_effects = self.get_active_effects(room_id, guest_id)
        
        # 쿨다운 상태 계산
        current_cooldowns = {}
        for (uid, item_id), end_time in self.cooldowns.items():
            if uid == guest_id:
                remaining = (end_time - datetime.utcnow()).total_seconds()
                if remaining > 0:
                    current_cooldowns[item_id] = int(remaining)
        
        return GameItemState(
            guest_id=guest_id,
            available_items=inventory,
            active_effects=active_effects,
            cooldowns=current_cooldowns,
            can_use_items=len(inventory) > 0
        )