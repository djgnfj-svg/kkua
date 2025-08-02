"""
아이템 서비스 테스트
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from services.item_service import ItemService
from models.item_model import Item, PlayerInventory, ItemUsageLog, DEFAULT_ITEMS
from models.guest_model import Guest
from schemas.item_schema import ItemUseRequest, ItemPurchaseRequest


@pytest.fixture
def mock_db():
    """Mock 데이터베이스 세션"""
    return Mock(spec=Session)


@pytest.fixture
def item_service(mock_db):
    """아이템 서비스 인스턴스"""
    return ItemService(mock_db)


@pytest.fixture
def sample_items():
    """테스트용 아이템들"""
    skip_turn = Item(
        item_id=1,
        name="턴 스킵",
        description="상대방의 턴을 건너뛰고 바로 내 턴으로 만듭니다",
        effect_type="skip_turn",
        effect_value=1,
        cost=15,
        cooldown_seconds=60,
        rarity="common",
        is_active=True
    )
    
    extra_time = Item(
        item_id=2,
        name="시간 연장",
        description="현재 턴의 제한 시간을 15초 추가합니다",
        effect_type="extra_time",
        effect_value=15,
        cost=10,
        cooldown_seconds=45,
        rarity="common",
        is_active=True
    )
    
    score_boost = Item(
        item_id=3,
        name="점수 배수",
        description="다음 단어의 점수를 2배로 받습니다",
        effect_type="score_multiplier",
        effect_value=2,
        cost=20,
        cooldown_seconds=90,
        rarity="rare",
        is_active=True
    )
    
    return [skip_turn, extra_time, score_boost]


@pytest.fixture
def sample_user():
    """테스트용 사용자"""
    return Guest(
        guest_id=1,
        uuid="test-uuid",
        nickname="테스트유저",
        session_token="test_token"
    )


class TestItemService:
    """아이템 서비스 테스트"""
    
    def test_initialize_default_items_first_time(self, item_service, mock_db):
        """최초 기본 아이템 초기화 테스트"""
        # Mock 설정: 기존 아이템 없음
        mock_db.query.return_value.count.return_value = 0
        
        # 테스트 실행
        result = item_service.initialize_default_items()
        
        # 검증
        assert result is True
        assert mock_db.add.call_count == len(DEFAULT_ITEMS)
        mock_db.commit.assert_called_once()
    
    def test_initialize_default_items_already_exists(self, item_service, mock_db):
        """이미 아이템이 있을 때 초기화 테스트"""
        # Mock 설정: 기존 아이템 있음
        mock_db.query.return_value.count.return_value = 5
        
        # 테스트 실행
        result = item_service.initialize_default_items()
        
        # 검증
        assert result is True
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
    
    def test_initialize_default_items_failure(self, item_service, mock_db):
        """기본 아이템 초기화 실패 테스트"""
        # Mock 설정: 데이터베이스 오류
        mock_db.query.return_value.count.return_value = 0
        mock_db.add.side_effect = Exception("Database error")
        
        # 테스트 실행
        result = item_service.initialize_default_items()
        
        # 검증
        assert result is False
        mock_db.rollback.assert_called_once()
    
    def test_get_all_items(self, item_service, mock_db, sample_items):
        """모든 활성 아이템 조회 테스트"""
        # Mock 설정
        mock_db.query.return_value.filter.return_value.all.return_value = sample_items
        
        # 테스트 실행
        result = item_service.get_all_items()
        
        # 검증
        assert len(result) == 3
        mock_db.query.assert_called_with(Item)
    
    def test_get_item_by_id_success(self, item_service, mock_db, sample_items):
        """ID로 아이템 조회 성공 테스트"""
        skip_turn = sample_items[0]
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.return_value = skip_turn
        
        # 테스트 실행
        result = item_service.get_item_by_id(1)
        
        # 검증
        assert result is not None
        assert result.item_id == 1
        assert result.name == "턴 스킵"
    
    def test_get_item_by_id_not_found(self, item_service, mock_db):
        """ID로 아이템 조회 실패 테스트"""
        # Mock 설정: 아이템 없음
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 테스트 실행
        result = item_service.get_item_by_id(999)
        
        # 검증
        assert result is None
    
    def test_get_player_inventory(self, item_service, mock_db, sample_user, sample_items):
        """플레이어 인벤토리 조회 테스트"""
        # Mock 인벤토리 데이터
        inventories = [
            PlayerInventory(
                inventory_id=1,
                guest_id=sample_user.guest_id,
                item_id=1,
                quantity=3,
                item=sample_items[0]
            ),
            PlayerInventory(
                inventory_id=2,
                guest_id=sample_user.guest_id,
                item_id=2,
                quantity=1,
                item=sample_items[1]
            )
        ]
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.all.return_value = inventories
        
        # 테스트 실행
        result = item_service.get_player_inventory(sample_user.guest_id)
        
        # 검증
        assert len(result) == 2
        assert result[0].quantity == 3
        assert result[1].quantity == 1
    
    def test_purchase_item_success(self, item_service, mock_db, sample_user, sample_items):
        """아이템 구매 성공 테스트"""
        extra_time = sample_items[1]
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            extra_time,  # 아이템 조회
            None         # 기존 인벤토리 없음
        ]
        
        # 테스트 데이터
        purchase_request = ItemPurchaseRequest(
            item_id=2,
            quantity=2,
            player_score=50  # 충분한 점수
        )
        
        # 테스트 실행
        result = item_service.purchase_item(sample_user, purchase_request)
        
        # 검증
        assert result.success is True
        assert result.remaining_score == 30  # 50 - (10 * 2)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_purchase_item_insufficient_score(self, item_service, mock_db, sample_user, sample_items):
        """점수 부족으로 아이템 구매 실패 테스트"""
        score_boost = sample_items[2]  # cost=20
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.return_value = score_boost
        
        # 테스트 데이터
        purchase_request = ItemPurchaseRequest(
            item_id=3,
            quantity=1,
            player_score=15  # 부족한 점수
        )
        
        # 테스트 실행
        result = item_service.purchase_item(sample_user, purchase_request)
        
        # 검증
        assert result.success is False
        assert "점수가 부족합니다" in result.message
        mock_db.add.assert_not_called()
    
    def test_purchase_item_existing_inventory(self, item_service, mock_db, sample_user, sample_items):
        """기존 인벤토리가 있는 아이템 구매 테스트"""
        skip_turn = sample_items[0]
        existing_inventory = PlayerInventory(
            inventory_id=1,
            guest_id=sample_user.guest_id,
            item_id=1,
            quantity=2
        )
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            skip_turn,           # 아이템 조회
            existing_inventory   # 기존 인벤토리
        ]
        
        # 테스트 데이터
        purchase_request = ItemPurchaseRequest(
            item_id=1,
            quantity=1,
            player_score=50
        )
        
        # 테스트 실행
        result = item_service.purchase_item(sample_user, purchase_request)
        
        # 검증
        assert result.success is True
        assert existing_inventory.quantity == 3  # 2 + 1
        mock_db.commit.assert_called_once()
    
    def test_use_item_success(self, item_service, mock_db, sample_user, sample_items):
        """아이템 사용 성공 테스트"""
        skip_turn = sample_items[0]
        inventory = PlayerInventory(
            inventory_id=1,
            guest_id=sample_user.guest_id,
            item_id=1,
            quantity=2,
            item=skip_turn
        )
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            skip_turn,   # 아이템 조회
            inventory    # 인벤토리 조회
        ]
        
        # 테스트 데이터
        use_request = ItemUseRequest(
            item_id=1,
            room_id=100,
            target_guest_id=None
        )
        
        # 테스트 실행
        result = item_service.use_item(sample_user, use_request)
        
        # 검증
        assert result.success is True
        assert result.effect_type == "skip_turn"
        assert inventory.quantity == 1  # 2 - 1
        mock_db.add.assert_called()  # ItemUsageLog 추가
        mock_db.commit.assert_called_once()
    
    def test_use_item_insufficient_quantity(self, item_service, mock_db, sample_user, sample_items):
        """수량 부족으로 아이템 사용 실패 테스트"""
        extra_time = sample_items[1]
        inventory = PlayerInventory(
            inventory_id=1,
            guest_id=sample_user.guest_id,
            item_id=2,
            quantity=0,  # 수량 없음
            item=extra_time
        )
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            extra_time,  # 아이템 조회
            inventory    # 인벤토리 조회
        ]
        
        # 테스트 데이터
        use_request = ItemUseRequest(
            item_id=2,
            room_id=100
        )
        
        # 테스트 실행
        result = item_service.use_item(sample_user, use_request)
        
        # 검증
        assert result.success is False
        assert "보유하고 있지 않습니다" in result.message
    
    def test_use_item_on_cooldown(self, item_service, mock_db, sample_user, sample_items):
        """쿨다운 중인 아이템 사용 테스트"""
        skip_turn = sample_items[0]
        inventory = PlayerInventory(
            inventory_id=1,
            guest_id=sample_user.guest_id,
            item_id=1,
            quantity=1,
            item=skip_turn
        )
        
        # 쿨다운 설정
        cooldown_key = (sample_user.guest_id, 1)
        item_service.cooldowns[cooldown_key] = datetime.utcnow() + timedelta(seconds=30)
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            skip_turn,   # 아이템 조회
            inventory    # 인벤토리 조회
        ]
        
        # 테스트 데이터
        use_request = ItemUseRequest(
            item_id=1,
            room_id=100
        )
        
        # 테스트 실행
        result = item_service.use_item(sample_user, use_request)
        
        # 검증
        assert result.success is False
        assert "쿨다운" in result.message
    
    def test_get_active_effects_for_room(self, item_service):
        """게임방의 활성 효과 조회 테스트"""
        room_id = 100
        guest_id = 1
        
        # 활성 효과 설정
        item_service.active_effects[room_id] = {
            guest_id: [
                {
                    "effect_type": "score_multiplier",
                    "effect_value": 2,
                    "remaining_turns": 1,
                    "applied_at": datetime.utcnow().isoformat()
                }
            ]
        }
        
        # 테스트 실행
        result = item_service.get_active_effects_for_room(room_id)
        
        # 검증
        assert guest_id in result
        assert len(result[guest_id]) == 1
        assert result[guest_id][0]["effect_type"] == "score_multiplier"
    
    def test_apply_item_effect_score_multiplier(self, item_service):
        """점수 배수 효과 적용 테스트"""
        room_id = 100
        guest_id = 1
        
        # 테스트 실행
        item_service.apply_item_effect(room_id, guest_id, "score_multiplier", 2, turns=1)
        
        # 검증
        effects = item_service.active_effects[room_id][guest_id]
        assert len(effects) == 1
        assert effects[0]["effect_type"] == "score_multiplier"
        assert effects[0]["effect_value"] == 2
        assert effects[0]["remaining_turns"] == 1
    
    def test_apply_item_effect_immunity(self, item_service):
        """면역 효과 적용 테스트"""
        room_id = 100
        guest_id = 1
        
        # 테스트 실행
        item_service.apply_item_effect(room_id, guest_id, "immunity", 1, turns=2)
        
        # 검증
        effects = item_service.active_effects[room_id][guest_id]
        assert len(effects) == 1
        assert effects[0]["effect_type"] == "immunity"
        assert effects[0]["remaining_turns"] == 2
    
    def test_check_immunity(self, item_service):
        """면역 상태 확인 테스트"""
        room_id = 100
        guest_id = 1
        
        # 면역 효과 적용
        item_service.apply_item_effect(room_id, guest_id, "immunity", 1, turns=1)
        
        # 테스트 실행
        is_immune = item_service.check_immunity(room_id, guest_id)
        
        # 검증
        assert is_immune is True
    
    def test_check_immunity_no_effect(self, item_service):
        """면역 효과가 없을 때 테스트"""
        room_id = 100
        guest_id = 1
        
        # 테스트 실행
        is_immune = item_service.check_immunity(room_id, guest_id)
        
        # 검증
        assert is_immune is False
    
    def test_update_effect_turns(self, item_service):
        """효과 턴 업데이트 테스트"""
        room_id = 100
        guest_id = 1
        
        # 여러 효과 적용
        item_service.apply_item_effect(room_id, guest_id, "score_multiplier", 2, turns=2)
        item_service.apply_item_effect(room_id, guest_id, "immunity", 1, turns=1)
        
        # 테스트 실행
        expired_effects = item_service.update_effect_turns(room_id, guest_id)
        
        # 검증
        remaining_effects = item_service.active_effects[room_id][guest_id]
        assert len(remaining_effects) == 1  # immunity는 만료됨
        assert remaining_effects[0]["effect_type"] == "score_multiplier"
        assert remaining_effects[0]["remaining_turns"] == 1
        
        assert len(expired_effects) == 1
        assert expired_effects[0]["effect_type"] == "immunity"
    
    def test_clear_room_effects(self, item_service):
        """게임방 효과 정리 테스트"""
        room_id = 100
        guest_id1 = 1
        guest_id2 = 2
        
        # 효과들 설정
        item_service.apply_item_effect(room_id, guest_id1, "score_multiplier", 2)
        item_service.apply_item_effect(room_id, guest_id2, "immunity", 1)
        
        # 테스트 실행
        item_service.clear_room_effects(room_id)
        
        # 검증
        assert room_id not in item_service.active_effects
    
    def test_get_cooldown_info(self, item_service, sample_user, sample_items):
        """쿨다운 정보 조회 테스트"""
        skip_turn = sample_items[0]
        
        # 쿨다운 설정
        cooldown_key = (sample_user.guest_id, 1)
        end_time = datetime.utcnow() + timedelta(seconds=45)
        item_service.cooldowns[cooldown_key] = end_time
        
        # 테스트 실행
        result = item_service.get_cooldown_info(sample_user.guest_id, [skip_turn])
        
        # 검증
        assert 1 in result
        assert result[1]["on_cooldown"] is True
        assert result[1]["remaining_seconds"] > 0
        assert result[1]["remaining_seconds"] <= 45
    
    def test_get_cooldown_info_no_cooldown(self, item_service, sample_user, sample_items):
        """쿨다운이 없는 아이템 정보 테스트"""
        extra_time = sample_items[1]
        
        # 테스트 실행
        result = item_service.get_cooldown_info(sample_user.guest_id, [extra_time])
        
        # 검증
        assert 2 in result
        assert result[2]["on_cooldown"] is False
        assert result[2]["remaining_seconds"] == 0
    
    def test_cleanup_expired_cooldowns(self, item_service, sample_user):
        """만료된 쿨다운 정리 테스트"""
        # 만료된 쿨다운과 유효한 쿨다운 설정
        expired_time = datetime.utcnow() - timedelta(seconds=10)
        valid_time = datetime.utcnow() + timedelta(seconds=30)
        
        item_service.cooldowns[(sample_user.guest_id, 1)] = expired_time
        item_service.cooldowns[(sample_user.guest_id, 2)] = valid_time
        
        # 테스트 실행
        item_service.cleanup_expired_cooldowns()
        
        # 검증
        assert (sample_user.guest_id, 1) not in item_service.cooldowns
        assert (sample_user.guest_id, 2) in item_service.cooldowns
    
    def test_get_item_usage_history(self, item_service, mock_db, sample_user):
        """아이템 사용 기록 조회 테스트"""
        # Mock 사용 기록
        usage_logs = [
            ItemUsageLog(
                usage_id=1,
                game_room_id=100,
                guest_id=sample_user.guest_id,
                item_id=1,
                used_at=datetime.utcnow(),
                effect_applied=True,
                game_round=1
            ),
            ItemUsageLog(
                usage_id=2,
                game_room_id=101,
                guest_id=sample_user.guest_id,
                item_id=2,
                used_at=datetime.utcnow(),
                effect_applied=True,
                game_round=3
            )
        ]
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = usage_logs
        
        # 테스트 실행
        result = item_service.get_item_usage_history(sample_user.guest_id, limit=10)
        
        # 검증
        assert len(result) == 2
        assert result[0].usage_id == 1
        assert result[1].usage_id == 2