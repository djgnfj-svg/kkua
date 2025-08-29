"""
아이템 시스템 서비스
아이템 관리, 효과 실행, 쿨다운 관리, 드롭 시스템
"""

import random
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from sqlalchemy import select, update
from database import get_db, get_redis
from models.item_models import Item
from models.user_models import UserItem
from redis_models import GameState, GamePlayer, WordChainState

logger = logging.getLogger(__name__)


class ItemRarity(str, Enum):
    """아이템 희귀도"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class ItemEffectType(str, Enum):
    """아이템 효과 타입"""
    TIME_EXTEND = "time_extend"        # 시간 연장
    SCORE_MULTIPLY = "score_multiply"  # 점수 배수
    WORD_HINT = "word_hint"           # 단어 힌트
    TIME_ATTACK = "time_attack"       # 상대방 시간 단축
    SHIELD = "shield"                 # 보호막
    FREEZE = "freeze"                 # 상대방 동결
    DOUBLE_TURN = "double_turn"       # 추가 턴
    WORD_STEAL = "word_steal"         # 단어 훔치기
    COMBO_BOOST = "combo_boost"       # 콤보 증가
    REVIVAL = "revival"               # 부활
    
    # 새로운 방해 아이템들
    CAT_DISTRACTION = "cat_distraction"    # 고양이 방해
    SCREEN_SHAKE = "screen_shake"          # 화면 흔들기
    BLUR_SCREEN = "blur_screen"            # 화면 흐림
    FALLING_OBJECTS = "falling_objects"    # 떨어지는 오브젝트
    COLOR_INVERT = "color_invert"          # 색상 반전


@dataclass
class ItemEffect:
    """아이템 효과 정보"""
    effect_type: ItemEffectType
    value: Dict[str, Any]
    duration: int = 0  # 효과 지속 시간 (초, 0이면 즉시 효과)
    target_type: str = "self"  # self, opponent, all
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "effect_type": self.effect_type,
            "value": self.value,
            "duration": self.duration,
            "target_type": self.target_type
        }


@dataclass
class ActiveEffect:
    """활성 효과"""
    item_id: int
    user_id: int
    effect: ItemEffect
    applied_at: datetime
    expires_at: Optional[datetime] = None
    
    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) >= self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "user_id": self.user_id,
            "effect": self.effect.to_dict(),
            "applied_at": self.applied_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired
        }


@dataclass
class ItemUseResult:
    """아이템 사용 결과"""
    success: bool
    message: str
    effect: Optional[ItemEffect] = None
    cooldown_until: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "effect": self.effect.to_dict() if self.effect else None,
            "cooldown_until": self.cooldown_until.isoformat() if self.cooldown_until else None
        }


class ItemService:
    """아이템 서비스"""
    
    def __init__(self):
        self.redis_client = get_redis()
        self.cooldown_prefix = "item_cooldown:"
        self.active_effects_prefix = "active_effects:"
        
        # 아이템 효과 매핑
        self.effect_handlers = {
            ItemEffectType.TIME_EXTEND: self._handle_time_extend,
            ItemEffectType.SCORE_MULTIPLY: self._handle_score_multiply,
            ItemEffectType.WORD_HINT: self._handle_word_hint,
            ItemEffectType.TIME_ATTACK: self._handle_time_attack,
            ItemEffectType.SHIELD: self._handle_shield,
            ItemEffectType.FREEZE: self._handle_freeze,
            ItemEffectType.DOUBLE_TURN: self._handle_double_turn,
            ItemEffectType.WORD_STEAL: self._handle_word_steal,
            ItemEffectType.COMBO_BOOST: self._handle_combo_boost,
            ItemEffectType.REVIVAL: self._handle_revival,
            
            # 새로운 방해 아이템 핸들러들
            ItemEffectType.CAT_DISTRACTION: self._handle_cat_distraction,
            ItemEffectType.SCREEN_SHAKE: self._handle_screen_shake,
            ItemEffectType.BLUR_SCREEN: self._handle_blur_screen,
            ItemEffectType.FALLING_OBJECTS: self._handle_falling_objects,
            ItemEffectType.COLOR_INVERT: self._handle_color_invert,
        }
    
    async def use_item(self, room_id: str, user_id: int, item_id: int, 
                      target_user_id: Optional[int] = None) -> ItemUseResult:
        """아이템 사용"""
        try:
            db = next(get_db())
            
            # 1. 아이템 보유 확인
            result = db.execute(
                select(UserItem, Item)
                .join(Item, UserItem.item_id == Item.id)
                .where(UserItem.user_id == user_id, UserItem.item_id == item_id, UserItem.quantity > 0)
            )
            user_item_data = result.first()
            
            if not user_item_data:
                return ItemUseResult(
                    success=False,
                    message="보유하지 않은 아이템입니다"
                )
            
            user_item, item = user_item_data
            
            # 2. 쿨다운 확인
            if await self._is_on_cooldown(user_id, item_id):
                cooldown_time = await self._get_cooldown_remaining(user_id, item_id)
                return ItemUseResult(
                    success=False,
                    message=f"쿨다운 중입니다 (남은 시간: {cooldown_time}초)"
                )
            
            # 3. 아이템 효과 생성
            effect = self._create_effect_from_item(item)
            
            # 4. 아이템 효과 실행
            execution_result = await self._execute_item_effect(
                room_id, user_id, effect, target_user_id
            )
            
            if not execution_result.success:
                return execution_result
            
            # 5. 아이템 소모
            user_item.quantity -= 1
            db.commit()
            
            # 6. 쿨다운 설정
            cooldown_until = None
            if item.cooldown_seconds > 0:
                cooldown_until = datetime.now(timezone.utc) + timedelta(seconds=item.cooldown_seconds)
                await self._set_cooldown(user_id, item_id, cooldown_until)
            
            logger.info(f"아이템 사용 성공: user_id={user_id}, item_id={item_id}, effect={effect.effect_type}")
            
            return ItemUseResult(
                success=True,
                message=f"{item.name} 아이템을 사용했습니다",
                effect=effect,
                cooldown_until=cooldown_until
            )
            
        except Exception as e:
            logger.error(f"아이템 사용 중 오류: {e}")
            return ItemUseResult(
                success=False,
                message="아이템 사용 중 오류가 발생했습니다"
            )
    
    def _create_effect_from_item(self, item: Item) -> ItemEffect:
        """아이템으로부터 효과 생성"""
        effect_type = ItemEffectType(item.effect_type)
        
        # 기본 효과 값 설정
        effect_values = {
            ItemEffectType.TIME_EXTEND: {"seconds": 10},
            ItemEffectType.SCORE_MULTIPLY: {"multiplier": 2.0},
            ItemEffectType.WORD_HINT: {"count": 3},
            ItemEffectType.TIME_ATTACK: {"seconds": 5},
            ItemEffectType.SHIELD: {"duration": 30},
            ItemEffectType.FREEZE: {"duration": 10},
            ItemEffectType.DOUBLE_TURN: {"extra_turns": 1},
            ItemEffectType.WORD_STEAL: {"count": 1},
            ItemEffectType.COMBO_BOOST: {"boost": 5},
            ItemEffectType.REVIVAL: {"health": 1},
        }
        
        # 아이템별 커스텀 값 적용
        value = item.effect_value if item.effect_value else effect_values.get(effect_type, {})
        
        # 타겟 타입 결정
        target_types = {
            ItemEffectType.TIME_EXTEND: "self",
            ItemEffectType.SCORE_MULTIPLY: "self",
            ItemEffectType.WORD_HINT: "self",
            ItemEffectType.TIME_ATTACK: "opponent",
            ItemEffectType.SHIELD: "self",
            ItemEffectType.FREEZE: "opponent",
            ItemEffectType.DOUBLE_TURN: "self",
            ItemEffectType.WORD_STEAL: "opponent",
            ItemEffectType.COMBO_BOOST: "self",
            ItemEffectType.REVIVAL: "self",
        }
        
        return ItemEffect(
            effect_type=effect_type,
            value=value,
            duration=value.get("duration", 0),
            target_type=target_types.get(effect_type, "self")
        )
    
    async def _execute_item_effect(self, room_id: str, user_id: int, effect: ItemEffect, 
                                 target_user_id: Optional[int] = None) -> ItemUseResult:
        """아이템 효과 실행"""
        try:
            # 효과 핸들러 호출
            handler = self.effect_handlers.get(effect.effect_type)
            if not handler:
                return ItemUseResult(
                    success=False,
                    message=f"지원되지 않는 아이템 효과입니다: {effect.effect_type}"
                )
            
            result = await handler(room_id, user_id, effect, target_user_id)
            
            # 지속 효과인 경우 활성 효과 목록에 추가
            if effect.duration > 0 and result.success:
                await self._add_active_effect(room_id, user_id, effect)
            
            return result
            
        except Exception as e:
            logger.error(f"아이템 효과 실행 중 오류: {e}")
            return ItemUseResult(
                success=False,
                message="아이템 효과 실행 중 오류가 발생했습니다"
            )
    
    # === 아이템 효과 핸들러들 ===
    
    async def _handle_time_extend(self, room_id: str, user_id: int, effect: ItemEffect, 
                                target_user_id: Optional[int] = None) -> ItemUseResult:
        """시간 연장 효과"""
        # 타이머 서비스와 연동하여 현재 턴 시간 연장
        from services.timer_service import get_timer_service
        timer_service = get_timer_service()
        
        seconds = effect.value.get("seconds", 10)
        success = await timer_service.extend_timer(room_id, user_id, seconds)
        
        if success:
            return ItemUseResult(
                success=True,
                message=f"턴 시간이 {seconds}초 연장되었습니다",
                effect=effect
            )
        else:
            return ItemUseResult(
                success=False,
                message="시간 연장에 실패했습니다"
            )
    
    async def _handle_score_multiply(self, room_id: str, user_id: int, effect: ItemEffect, 
                                   target_user_id: Optional[int] = None) -> ItemUseResult:
        """점수 배수 효과"""
        multiplier = effect.value.get("multiplier", 2.0)
        
        # 활성 효과 목록에 추가 (다음 단어 제출 시 적용)
        await self._add_active_effect(room_id, user_id, effect)
        
        return ItemUseResult(
            success=True,
            message=f"다음 단어 점수가 {multiplier}배가 됩니다",
            effect=effect
        )
    
    async def _handle_word_hint(self, room_id: str, user_id: int, effect: ItemEffect, 
                              target_user_id: Optional[int] = None) -> ItemUseResult:
        """단어 힌트 효과"""
        from services.word_validator import get_word_validator
        from services.game_engine import get_game_engine
        
        word_validator = get_word_validator()
        game_engine = get_game_engine()
        
        game_state = await game_engine.get_game_state(room_id)
        if not game_state or not game_state.word_chain:
            return ItemUseResult(
                success=False,
                message="게임 상태를 찾을 수 없습니다"
            )
        
        last_char = game_state.word_chain.last_char
        if not last_char:
            return ItemUseResult(
                success=False,
                message="아직 단어가 제출되지 않았습니다"
            )
        
        count = effect.value.get("count", 3)
        hints = await word_validator.get_word_hints(last_char, count)
        
        return ItemUseResult(
            success=True,
            message=f"단어 힌트: {', '.join(hints)}",
            effect=effect
        )
    
    async def _handle_time_attack(self, room_id: str, user_id: int, effect: ItemEffect, 
                                target_user_id: Optional[int] = None) -> ItemUseResult:
        """시간 공격 효과"""
        from services.timer_service import get_timer_service
        from services.game_engine import get_game_engine
        
        timer_service = get_timer_service()
        game_engine = get_game_engine()
        
        # 대상 결정 (지정되지 않으면 현재 턴 플레이어)
        if not target_user_id:
            game_state = await game_engine.get_game_state(room_id)
            if game_state:
                target_user_id = game_state.current_turn
        
        if not target_user_id or target_user_id == user_id:
            return ItemUseResult(
                success=False,
                message="공격할 대상이 없습니다"
            )
        
        seconds = effect.value.get("seconds", 5)
        success = await timer_service.reduce_timer(room_id, target_user_id, seconds)
        
        if success:
            return ItemUseResult(
                success=True,
                message=f"상대방의 시간을 {seconds}초 단축했습니다",
                effect=effect
            )
        else:
            return ItemUseResult(
                success=False,
                message="시간 공격에 실패했습니다"
            )
    
    async def _handle_shield(self, room_id: str, user_id: int, effect: ItemEffect, 
                           target_user_id: Optional[int] = None) -> ItemUseResult:
        """보호막 효과"""
        duration = effect.value.get("duration", 30)
        
        # 활성 효과로 등록
        await self._add_active_effect(room_id, user_id, effect)
        
        return ItemUseResult(
            success=True,
            message=f"{duration}초 동안 아이템 공격에 면역됩니다",
            effect=effect
        )
    
    async def _handle_freeze(self, room_id: str, user_id: int, effect: ItemEffect, 
                           target_user_id: Optional[int] = None) -> ItemUseResult:
        """동결 효과"""
        from services.game_engine import get_game_engine
        
        game_engine = get_game_engine()
        
        # 대상 결정
        if not target_user_id:
            game_state = await game_engine.get_game_state(room_id)
            if game_state:
                target_user_id = game_state.current_turn
        
        if not target_user_id or target_user_id == user_id:
            return ItemUseResult(
                success=False,
                message="동결할 대상이 없습니다"
            )
        
        duration = effect.value.get("duration", 10)
        
        # 대상에게 동결 효과 적용
        await self._add_active_effect(room_id, target_user_id, effect)
        
        return ItemUseResult(
            success=True,
            message=f"상대방을 {duration}초 동안 동결시켰습니다",
            effect=effect
        )
    
    async def _handle_double_turn(self, room_id: str, user_id: int, effect: ItemEffect, 
                                target_user_id: Optional[int] = None) -> ItemUseResult:
        """추가 턴 효과"""
        extra_turns = effect.value.get("extra_turns", 1)
        
        # 활성 효과로 등록
        await self._add_active_effect(room_id, user_id, effect)
        
        return ItemUseResult(
            success=True,
            message=f"{extra_turns}번의 추가 턴을 얻었습니다",
            effect=effect
        )
    
    async def _handle_word_steal(self, room_id: str, user_id: int, effect: ItemEffect, 
                               target_user_id: Optional[int] = None) -> ItemUseResult:
        """단어 훔치기 효과"""
        return ItemUseResult(
            success=True,
            message="단어 훔치기 효과가 적용되었습니다 (구현 예정)",
            effect=effect
        )
    
    async def _handle_combo_boost(self, room_id: str, user_id: int, effect: ItemEffect, 
                                target_user_id: Optional[int] = None) -> ItemUseResult:
        """콤보 증가 효과"""
        from services.game_engine import get_game_engine
        
        game_engine = get_game_engine()
        game_state = await game_engine.get_game_state(room_id)
        
        if not game_state:
            return ItemUseResult(
                success=False,
                message="게임 상태를 찾을 수 없습니다"
            )
        
        boost = effect.value.get("boost", 5)
        
        # 콤보 증가
        if game_state.word_chain:
            game_state.word_chain.combo_count += boost
            await game_engine._update_game_state(room_id, game_state)
        
        return ItemUseResult(
            success=True,
            message=f"콤보가 {boost} 증가했습니다",
            effect=effect
        )
    
    async def _handle_revival(self, room_id: str, user_id: int, effect: ItemEffect, 
                            target_user_id: Optional[int] = None) -> ItemUseResult:
        """부활 효과"""
        from services.game_engine import get_game_engine
        
        game_engine = get_game_engine()
        game_state = await game_engine.get_game_state(room_id)
        
        if not game_state:
            return ItemUseResult(
                success=False,
                message="게임 상태를 찾을 수 없습니다"
            )
        
        player = game_state.players.get(str(user_id))
        if not player:
            return ItemUseResult(
                success=False,
                message="플레이어를 찾을 수 없습니다"
            )
        
        # 부활 아이템은 탈락 시스템이 없어져서 사용할 수 없음
        # 점수 보너스로 대체
        player.score += 50
        await game_engine._update_game_state(room_id, game_state)
        
        return ItemUseResult(
            success=True,
            message="부활했습니다!",
            effect=effect
        )
    
    # 새로운 방해 아이템 핸들러들
    async def _handle_cat_distraction(self, room_id: str, user_id: int, effect: ItemEffect, 
                                    target_user_id: Optional[int] = None) -> ItemUseResult:
        """고양이 방해 효과"""
        duration = effect.value.get("duration", 5)
        cat_count = effect.value.get("cat_count", 3)
        
        # 모든 상대방에게 적용
        from services.game_engine import get_game_engine
        game_engine = get_game_engine()
        game_state = await game_engine.get_game_state(room_id)
        
        if not game_state:
            return ItemUseResult(
                success=False,
                message="게임 상태를 찾을 수 없습니다"
            )
        
        # 사용자를 제외한 모든 플레이어에게 효과 적용
        targets_applied = 0
        for player_id in game_state.players.keys():
            if int(player_id) != user_id:
                await self._add_active_effect(room_id, int(player_id), effect)
                targets_applied += 1
        
        return ItemUseResult(
            success=True,
            message=f"고양이 {cat_count}마리가 {duration}초간 상대방을 방해합니다 😸",
            effect=effect,
            targets_affected=targets_applied
        )
    
    async def _handle_screen_shake(self, room_id: str, user_id: int, effect: ItemEffect, 
                                 target_user_id: Optional[int] = None) -> ItemUseResult:
        """화면 흔들기 효과"""
        duration = effect.value.get("duration", 3)
        intensity = effect.value.get("intensity", "medium")
        
        # 대상 선정 (지정되지 않으면 현재 턴 플레이어)
        if not target_user_id:
            from services.game_engine import get_game_engine
            game_engine = get_game_engine()
            game_state = await game_engine.get_game_state(room_id)
            if game_state:
                target_user_id = game_state.current_turn
        
        if not target_user_id or target_user_id == user_id:
            return ItemUseResult(
                success=False,
                message="방해할 대상이 없습니다"
            )
        
        await self._add_active_effect(room_id, target_user_id, effect)
        
        return ItemUseResult(
            success=True,
            message=f"상대방의 화면이 {duration}초간 흔들립니다 📳",
            effect=effect
        )
    
    async def _handle_blur_screen(self, room_id: str, user_id: int, effect: ItemEffect, 
                                target_user_id: Optional[int] = None) -> ItemUseResult:
        """화면 흐림 효과"""
        duration = effect.value.get("duration", 4)
        blur_level = effect.value.get("blur_level", 3)
        
        if not target_user_id:
            from services.game_engine import get_game_engine
            game_engine = get_game_engine()
            game_state = await game_engine.get_game_state(room_id)
            if game_state:
                target_user_id = game_state.current_turn
        
        if not target_user_id or target_user_id == user_id:
            return ItemUseResult(
                success=False,
                message="방해할 대상이 없습니다"
            )
        
        await self._add_active_effect(room_id, target_user_id, effect)
        
        return ItemUseResult(
            success=True,
            message=f"상대방의 화면이 {duration}초간 흐려집니다 😵‍💫",
            effect=effect
        )
    
    async def _handle_falling_objects(self, room_id: str, user_id: int, effect: ItemEffect, 
                                    target_user_id: Optional[int] = None) -> ItemUseResult:
        """떨어지는 오브젝트 효과"""
        duration = effect.value.get("duration", 6)
        object_type = effect.value.get("object_type", "leaves")
        
        # 모든 상대방에게 적용
        from services.game_engine import get_game_engine
        game_engine = get_game_engine()
        game_state = await game_engine.get_game_state(room_id)
        
        if not game_state:
            return ItemUseResult(
                success=False,
                message="게임 상태를 찾을 수 없습니다"
            )
        
        targets_applied = 0
        for player_id in game_state.players.keys():
            if int(player_id) != user_id:
                await self._add_active_effect(room_id, int(player_id), effect)
                targets_applied += 1
        
        object_emoji = {
            "leaves": "🍃",
            "hearts": "💕",
            "stars": "⭐",
            "snow": "❄️"
        }.get(object_type, "🍃")
        
        return ItemUseResult(
            success=True,
            message=f"{object_emoji} {duration}초간 하늘에서 떨어집니다",
            effect=effect,
            targets_affected=targets_applied
        )
    
    async def _handle_color_invert(self, room_id: str, user_id: int, effect: ItemEffect, 
                                 target_user_id: Optional[int] = None) -> ItemUseResult:
        """색상 반전 효과"""
        duration = effect.value.get("duration", 5)
        
        if not target_user_id:
            from services.game_engine import get_game_engine
            game_engine = get_game_engine()
            game_state = await game_engine.get_game_state(room_id)
            if game_state:
                target_user_id = game_state.current_turn
        
        if not target_user_id or target_user_id == user_id:
            return ItemUseResult(
                success=False,
                message="방해할 대상이 없습니다"
            )
        
        await self._add_active_effect(room_id, target_user_id, effect)
        
        return ItemUseResult(
            success=True,
            message=f"상대방의 화면 색상이 {duration}초간 반전됩니다 🎨",
            effect=effect
        )
    
    # === 쿨다운 관리 ===
    
    async def _is_on_cooldown(self, user_id: int, item_id: int) -> bool:
        """쿨다운 상태 확인"""
        key = f"{self.cooldown_prefix}{user_id}:{item_id}"
        cooldown_data = self.redis_client.get(key)
        
        if not cooldown_data:
            return False
        
        cooldown_until = datetime.fromisoformat(cooldown_data.decode())
        return datetime.now(timezone.utc) < cooldown_until
    
    async def _set_cooldown(self, user_id: int, item_id: int, until: datetime):
        """쿨다운 설정"""
        key = f"{self.cooldown_prefix}{user_id}:{item_id}"
        ttl = int((until - datetime.now(timezone.utc)).total_seconds())
        
        if ttl > 0:
            self.redis_client.setex(key, ttl, until.isoformat())
    
    async def _get_cooldown_remaining(self, user_id: int, item_id: int) -> int:
        """남은 쿨다운 시간 반환 (초)"""
        key = f"{self.cooldown_prefix}{user_id}:{item_id}"
        cooldown_data = self.redis_client.get(key)
        
        if not cooldown_data:
            return 0
        
        cooldown_until = datetime.fromisoformat(cooldown_data.decode())
        remaining = (cooldown_until - datetime.now(timezone.utc)).total_seconds()
        return max(0, int(remaining))
    
    # === 활성 효과 관리 ===
    
    async def _add_active_effect(self, room_id: str, user_id: int, effect: ItemEffect):
        """활성 효과 추가"""
        key = f"{self.active_effects_prefix}{room_id}:{user_id}"
        
        active_effect = ActiveEffect(
            item_id=0,  # 임시
            user_id=user_id,
            effect=effect,
            applied_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=effect.duration) if effect.duration > 0 else None
        )
        
        # Redis에 저장
        ttl = effect.duration if effect.duration > 0 else 3600  # 1시간 기본 TTL
        self.redis_client.setex(
            key,
            ttl,
            json.dumps(active_effect.to_dict(), ensure_ascii=False)
        )
    
    async def get_active_effects(self, room_id: str, user_id: int) -> List[ActiveEffect]:
        """활성 효과 목록 조회"""
        key = f"{self.active_effects_prefix}{room_id}:{user_id}"
        effect_data = self.redis_client.get(key)
        
        if not effect_data:
            return []
        
        try:
            data = json.loads(effect_data)
            effect = ItemEffect(
                effect_type=ItemEffectType(data["effect"]["effect_type"]),
                value=data["effect"]["value"],
                duration=data["effect"]["duration"],
                target_type=data["effect"]["target_type"]
            )
            
            active_effect = ActiveEffect(
                item_id=data["item_id"],
                user_id=data["user_id"],
                effect=effect,
                applied_at=datetime.fromisoformat(data["applied_at"]),
                expires_at=datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None
            )
            
            # 만료된 효과 제거
            if active_effect.is_expired:
                self.redis_client.delete(key)
                return []
            
            return [active_effect]
            
        except Exception as e:
            logger.error(f"활성 효과 파싱 중 오류: {e}")
            return []
    
    async def clear_active_effects(self, room_id: str, user_id: int):
        """활성 효과 모두 제거"""
        key = f"{self.active_effects_prefix}{room_id}:{user_id}"
        self.redis_client.delete(key)
    
    # === 아이템 드롭 시스템 ===
    
    async def drop_random_item(self, user_id: int, game_performance: Dict[str, Any]) -> Optional[Item]:
        """게임 성과 기반 랜덤 아이템 드롭"""
        try:
            db = next(get_db())
            
            # 모든 활성 아이템 조회
            result = db.execute(select(Item).where(Item.is_active == True))
            available_items = result.fetchall()
            
            if not available_items:
                return None
            
            # 성과 기반 드롭률 조정
            base_drop_chance = 0.7  # 기본 70% 확률
            performance_bonus = self._calculate_performance_bonus(game_performance)
            final_drop_chance = min(0.95, base_drop_chance + performance_bonus)
            
            # 드롭 여부 결정
            if random.random() > final_drop_chance:
                return None
            
            # 희귀도 기반 가중 선택
            weighted_items = []
            for item in available_items:
                weight = 1.0 / Item.get_rarity_drop_rate(item.rarity)
                weighted_items.extend([item] * int(weight * 100))
            
            if not weighted_items:
                return None
            
            # 랜덤 선택
            selected_item = random.choice(weighted_items)
            
            # 사용자 인벤토리에 추가
            await self._add_item_to_inventory(user_id, selected_item.id, 1)
            
            logger.info(f"아이템 드롭: user_id={user_id}, item={selected_item.name}")
            return selected_item
            
        except Exception as e:
            logger.error(f"아이템 드롭 중 오류: {e}")
            return None
    
    def _calculate_performance_bonus(self, performance: Dict[str, Any]) -> float:
        """게임 성과 기반 드롭률 보너스 계산"""
        bonus = 0.0
        
        # 점수 기반 보너스
        score = performance.get("score", 0)
        if score >= 1000:
            bonus += 0.1
        elif score >= 500:
            bonus += 0.05
        
        # 순위 기반 보너스
        rank = performance.get("rank", 4)
        if rank == 1:
            bonus += 0.15
        elif rank == 2:
            bonus += 0.1
        elif rank == 3:
            bonus += 0.05
        
        # 콤보 기반 보너스
        max_combo = performance.get("max_combo", 0)
        if max_combo >= 10:
            bonus += 0.1
        elif max_combo >= 5:
            bonus += 0.05
        
        # 정확도 기반 보너스
        accuracy = performance.get("accuracy", 0)
        if accuracy >= 0.9:
            bonus += 0.1
        elif accuracy >= 0.7:
            bonus += 0.05
        
        return min(0.25, bonus)  # 최대 25% 보너스
    
    async def _add_item_to_inventory(self, user_id: int, item_id: int, quantity: int = 1):
        """인벤토리에 아이템 추가"""
        try:
            db = next(get_db())
            
            # 기존 아이템 확인
            result = db.execute(
                select(UserItem).where(UserItem.user_id == user_id, UserItem.item_id == item_id)
            )
            existing_item = result.scalar_one_or_none()
            
            if existing_item:
                # 수량 증가
                existing_item.quantity += quantity
            else:
                # 새 아이템 추가
                new_user_item = UserItem(
                    user_id=user_id,
                    item_id=item_id,
                    quantity=quantity
                )
                db.add(new_user_item)
            
            db.commit()
            logger.info(f"아이템 인벤토리 추가: user_id={user_id}, item_id={item_id}, quantity={quantity}")
            
        except Exception as e:
            logger.error(f"아이템 인벤토리 추가 중 오류: {e}")
            db.rollback()
    
    async def get_user_inventory(self, user_id: int) -> List[Dict[str, Any]]:
        """사용자 인벤토리 조회"""
        try:
            db = next(get_db())
            
            result = db.execute(
                select(UserItem, Item)
                .join(Item, UserItem.item_id == Item.id)
                .where(UserItem.user_id == user_id, UserItem.quantity > 0)
                .order_by(Item.rarity, Item.name)
            )
            
            inventory = []
            for user_item, item in result.fetchall():
                cooldown_remaining = await self._get_cooldown_remaining(user_id, item.id)
                
                inventory.append({
                    "item": item.to_dict(),
                    "quantity": user_item.quantity,
                    "cooldown_remaining": cooldown_remaining,
                    "can_use": cooldown_remaining == 0
                })
            
            return inventory
            
        except Exception as e:
            logger.error(f"인벤토리 조회 중 오류: {e}")
            return []

    async def get_all_items(self) -> List[Dict[str, Any]]:
        """모든 활성 아이템 목록 조회"""
        try:
            db = next(get_db())
            
            result = db.execute(
                select(Item)
                .where(Item.is_active == True)
                .order_by(Item.rarity, Item.name)
            )
            
            items = []
            for row in result.fetchall():
                item = row[0]  # Row 객체에서 Item 인스턴스 추출
                items.append(item.to_dict())
            
            return items
            
        except Exception as e:
            logger.error(f"아이템 목록 조회 중 오류: {e}")
            return []
    
    async def give_startup_item(self, user_id: int) -> Optional[Item]:
        """게임 시작 시 플레이어에게 랜덤 아이템 1개 지급"""
        try:
            db = next(get_db())
            
            # 모든 활성 아이템 조회
            result = db.execute(select(Item).where(Item.is_active == True))
            available_items = result.scalars().all()
            
            if not available_items:
                logger.warning("지급 가능한 아이템이 없습니다")
                return None
            
            # 희귀도별 가중치 설정 (일반 아이템이 더 많이 나오도록)
            weighted_items = []
            for item in available_items:
                # 희귀도가 낮을수록 더 많은 가중치
                if item.rarity == "common":
                    weight = 50
                elif item.rarity == "uncommon":
                    weight = 25
                elif item.rarity == "rare":
                    weight = 15
                elif item.rarity == "epic":
                    weight = 8
                elif item.rarity == "legendary":
                    weight = 2
                else:
                    weight = 10  # 기본값
                
                weighted_items.extend([item] * weight)
            
            # 랜덤 선택
            selected_item = random.choice(weighted_items)
            
            # 인벤토리에 추가
            await self._add_item_to_inventory(user_id, selected_item.id, 1)
            
            logger.info(f"게임 시작 아이템 지급: user_id={user_id}, item={selected_item.name}")
            return selected_item
            
        except Exception as e:
            logger.error(f"게임 시작 아이템 지급 중 오류: {e}")
            return None


# 전역 아이템 서비스 인스턴스
item_service = ItemService()


def get_item_service() -> ItemService:
    """아이템 서비스 의존성"""
    return item_service