"""
아이템 모델 테스트
"""

import pytest
from datetime import datetime
from models.item_model import Item, PlayerInventory, ItemUsageLog, DEFAULT_ITEMS
from models.guest_model import Guest


@pytest.fixture
def sample_guest(db_session):
    """테스트용 게스트 사용자"""
    guest = Guest(
        uuid="test-uuid-item",
        nickname="아이템테스터",
        session_token="item_token"
    )
    db_session.add(guest)
    db_session.commit()
    db_session.refresh(guest)
    return guest


@pytest.fixture
def sample_item(db_session):
    """테스트용 아이템"""
    item = Item(
        name="테스트 아이템",
        description="테스트용 아이템입니다",
        effect_type="test_effect",
        effect_value=5,
        cost=15,
        cooldown_seconds=30,
        rarity="common"
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


class TestItemModel:
    """아이템 모델 테스트"""
    
    def test_create_item(self, db_session):
        """아이템 생성 테스트"""
        item = Item(
            name="시간 연장",
            description="턴 시간을 15초 연장합니다",
            effect_type="extra_time",
            effect_value=15,
            cost=10,
            cooldown_seconds=60,
            rarity="common",
            is_active=True
        )
        
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        
        assert item.item_id is not None
        assert item.name == "시간 연장"
        assert item.description == "턴 시간을 15초 연장합니다"
        assert item.effect_type == "extra_time"
        assert item.effect_value == 15
        assert item.cost == 10
        assert item.cooldown_seconds == 60
        assert item.rarity == "common"
        assert item.is_active is True
        assert item.created_at is not None
        assert item.updated_at is not None
    
    def test_item_defaults(self, db_session):
        """아이템 기본값 테스트"""
        item = Item(
            name="기본 아이템",
            effect_type="basic_effect"
        )
        
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        
        assert item.effect_value == 0
        assert item.cost == 10
        assert item.cooldown_seconds == 60
        assert item.rarity == "common"
        assert item.is_active is True
    
    def test_item_effect_types(self, db_session):
        """다양한 아이템 효과 타입 테스트"""
        items = [
            Item(name="턴 스킵", effect_type="skip_turn", effect_value=1),
            Item(name="시간 연장", effect_type="extra_time", effect_value=15),
            Item(name="점수 배수", effect_type="score_multiplier", effect_value=2),
            Item(name="단어 힌트", effect_type="word_hint", effect_value=1),
            Item(name="보호막", effect_type="immunity", effect_value=1),
        ]
        
        db_session.add_all(items)
        db_session.commit()
        
        for item in items:
            assert item.item_id is not None
            assert item.effect_type in ["skip_turn", "extra_time", "score_multiplier", "word_hint", "immunity"]
    
    def test_item_rarity_levels(self, db_session):
        """아이템 희귀도 레벨 테스트"""
        items = [
            Item(name="일반 아이템", effect_type="basic", rarity="common", cost=10),
            Item(name="희귀 아이템", effect_type="rare", rarity="rare", cost=20),
            Item(name="에픽 아이템", effect_type="epic", rarity="epic", cost=50),
        ]
        
        db_session.add_all(items)
        db_session.commit()
        
        common_items = db_session.query(Item).filter(Item.rarity == "common").all()
        rare_items = db_session.query(Item).filter(Item.rarity == "rare").all()
        epic_items = db_session.query(Item).filter(Item.rarity == "epic").all()
        
        assert len(common_items) == 1
        assert len(rare_items) == 1
        assert len(epic_items) == 1
    
    def test_item_active_inactive(self, db_session):
        """아이템 활성/비활성 테스트"""
        active_item = Item(
            name="활성 아이템",
            effect_type="active_effect",
            is_active=True
        )
        
        inactive_item = Item(
            name="비활성 아이템",
            effect_type="inactive_effect",
            is_active=False
        )
        
        db_session.add_all([active_item, inactive_item])
        db_session.commit()
        
        active_items = db_session.query(Item).filter(Item.is_active == True).all()
        assert len(active_items) == 1
        assert active_items[0].name == "활성 아이템"


class TestPlayerInventoryModel:
    """플레이어 인벤토리 모델 테스트"""
    
    def test_create_player_inventory(self, db_session, sample_guest, sample_item):
        """플레이어 인벤토리 생성 테스트"""
        inventory = PlayerInventory(
            guest_id=sample_guest.guest_id,
            item_id=sample_item.item_id,
            quantity=3
        )
        
        db_session.add(inventory)
        db_session.commit()
        db_session.refresh(inventory)
        
        assert inventory.inventory_id is not None
        assert inventory.guest_id == sample_guest.guest_id
        assert inventory.item_id == sample_item.item_id
        assert inventory.quantity == 3
        assert inventory.acquired_at is not None
    
    def test_player_inventory_default_quantity(self, db_session, sample_guest, sample_item):
        """인벤토리 기본 수량 테스트"""
        inventory = PlayerInventory(
            guest_id=sample_guest.guest_id,
            item_id=sample_item.item_id
        )
        
        db_session.add(inventory)
        db_session.commit()
        db_session.refresh(inventory)
        
        assert inventory.quantity == 1
    
    def test_player_inventory_relationship(self, db_session, sample_guest, sample_item):
        """인벤토리 관계 테스트"""
        inventory = PlayerInventory(
            guest_id=sample_guest.guest_id,
            item_id=sample_item.item_id,
            quantity=2
        )
        
        db_session.add(inventory)
        db_session.commit()
        db_session.refresh(inventory)
        
        # 아이템 관계 확인
        assert inventory.item is not None
        assert inventory.item.item_id == sample_item.item_id
        assert inventory.item.name == sample_item.name
    
    def test_multiple_items_same_player(self, db_session, sample_guest):
        """같은 플레이어가 여러 아이템을 소유하는 테스트"""
        item1 = Item(name="아이템1", effect_type="effect1")
        item2 = Item(name="아이템2", effect_type="effect2")
        
        db_session.add_all([item1, item2])
        db_session.commit()
        
        inventory1 = PlayerInventory(
            guest_id=sample_guest.guest_id,
            item_id=item1.item_id,
            quantity=2
        )
        
        inventory2 = PlayerInventory(
            guest_id=sample_guest.guest_id,
            item_id=item2.item_id,
            quantity=1
        )
        
        db_session.add_all([inventory1, inventory2])
        db_session.commit()
        
        # 플레이어의 모든 인벤토리 조회
        inventories = db_session.query(PlayerInventory).filter(
            PlayerInventory.guest_id == sample_guest.guest_id
        ).all()
        
        assert len(inventories) == 2
        total_quantity = sum(inv.quantity for inv in inventories)
        assert total_quantity == 3


class TestItemUsageLogModel:
    """아이템 사용 기록 모델 테스트"""
    
    def test_create_item_usage_log(self, db_session, sample_guest, sample_item):
        """아이템 사용 기록 생성 테스트"""
        usage_log = ItemUsageLog(
            game_room_id=123,
            guest_id=sample_guest.guest_id,
            item_id=sample_item.item_id,
            effect_applied=True,
            game_round=5
        )
        
        db_session.add(usage_log)
        db_session.commit()
        db_session.refresh(usage_log)
        
        assert usage_log.usage_id is not None
        assert usage_log.game_room_id == 123
        assert usage_log.guest_id == sample_guest.guest_id
        assert usage_log.item_id == sample_item.item_id
        assert usage_log.effect_applied is True
        assert usage_log.game_round == 5
        assert usage_log.used_at is not None
    
    def test_item_usage_log_defaults(self, db_session, sample_guest, sample_item):
        """아이템 사용 기록 기본값 테스트"""
        usage_log = ItemUsageLog(
            game_room_id=456,
            guest_id=sample_guest.guest_id,
            item_id=sample_item.item_id
        )
        
        db_session.add(usage_log)
        db_session.commit()
        db_session.refresh(usage_log)
        
        assert usage_log.effect_applied is True
        assert usage_log.game_round == 1
        assert usage_log.target_guest_id is None
    
    def test_item_usage_with_target(self, db_session, sample_item):
        """대상이 있는 아이템 사용 기록 테스트"""
        # 사용자와 대상 사용자 생성
        user = Guest(uuid="user-uuid", nickname="사용자", session_token="user_token")
        target = Guest(uuid="target-uuid", nickname="대상자", session_token="target_token")
        
        db_session.add_all([user, target])
        db_session.commit()
        db_session.refresh(user)
        db_session.refresh(target)
        
        usage_log = ItemUsageLog(
            game_room_id=789,
            guest_id=user.guest_id,
            item_id=sample_item.item_id,
            target_guest_id=target.guest_id,
            game_round=3
        )
        
        db_session.add(usage_log)
        db_session.commit()
        db_session.refresh(usage_log)
        
        assert usage_log.guest_id == user.guest_id
        assert usage_log.target_guest_id == target.guest_id
    
    def test_item_usage_log_relationship(self, db_session, sample_guest, sample_item):
        """아이템 사용 기록 관계 테스트"""
        usage_log = ItemUsageLog(
            game_room_id=999,
            guest_id=sample_guest.guest_id,
            item_id=sample_item.item_id
        )
        
        db_session.add(usage_log)
        db_session.commit()
        db_session.refresh(usage_log)
        
        # 아이템 관계 확인
        assert usage_log.item is not None
        assert usage_log.item.item_id == sample_item.item_id
        assert usage_log.item.name == sample_item.name
    
    def test_multiple_usage_logs_same_game(self, db_session, sample_guest, sample_item):
        """같은 게임에서 여러 아이템 사용 기록 테스트"""
        room_id = 555
        
        logs = [
            ItemUsageLog(
                game_room_id=room_id,
                guest_id=sample_guest.guest_id,
                item_id=sample_item.item_id,
                game_round=1
            ),
            ItemUsageLog(
                game_room_id=room_id,
                guest_id=sample_guest.guest_id,
                item_id=sample_item.item_id,
                game_round=3
            ),
            ItemUsageLog(
                game_room_id=room_id,
                guest_id=sample_guest.guest_id,
                item_id=sample_item.item_id,
                game_round=5
            )
        ]
        
        db_session.add_all(logs)
        db_session.commit()
        
        # 특정 게임방의 사용 기록 조회
        game_logs = db_session.query(ItemUsageLog).filter(
            ItemUsageLog.game_room_id == room_id
        ).order_by(ItemUsageLog.game_round).all()
        
        assert len(game_logs) == 3
        assert game_logs[0].game_round == 1
        assert game_logs[1].game_round == 3
        assert game_logs[2].game_round == 5


class TestDefaultItemsData:
    """기본 아이템 데이터 테스트"""
    
    def test_default_items_structure(self):
        """기본 아이템 데이터 구조 테스트"""
        assert isinstance(DEFAULT_ITEMS, list)
        assert len(DEFAULT_ITEMS) > 0
        
        for item_data in DEFAULT_ITEMS:
            # 필수 필드 확인
            assert "name" in item_data
            assert "description" in item_data
            assert "effect_type" in item_data
            assert "effect_value" in item_data
            assert "cost" in item_data
            assert "cooldown_seconds" in item_data
            assert "rarity" in item_data
            
            # 타입 확인
            assert isinstance(item_data["name"], str)
            assert isinstance(item_data["description"], str)
            assert isinstance(item_data["effect_type"], str)
            assert isinstance(item_data["effect_value"], int)
            assert isinstance(item_data["cost"], int)
            assert isinstance(item_data["cooldown_seconds"], int)
            assert isinstance(item_data["rarity"], str)
    
    def test_default_items_effect_types(self):
        """기본 아이템 효과 타입 테스트"""
        effect_types = [item["effect_type"] for item in DEFAULT_ITEMS]
        
        # 예상되는 효과 타입들이 포함되어 있는지 확인
        expected_types = ["skip_turn", "extra_time", "score_multiplier", "word_hint", "immunity"]
        
        for expected_type in expected_types:
            assert expected_type in effect_types
    
    def test_default_items_rarity_distribution(self):
        """기본 아이템 희귀도 분포 테스트"""
        rarities = [item["rarity"] for item in DEFAULT_ITEMS]
        
        # 다양한 희귀도가 포함되어 있는지 확인
        assert "common" in rarities
        assert "rare" in rarities
        
        # common 아이템이 가장 많은지 확인
        common_count = rarities.count("common")
        rare_count = rarities.count("rare")
        
        assert common_count >= rare_count
    
    def test_default_items_cost_balance(self):
        """기본 아이템 비용 밸런스 테스트"""
        costs = [item["cost"] for item in DEFAULT_ITEMS]
        
        # 비용 범위 확인
        assert all(cost > 0 for cost in costs)
        assert any(cost <= 15 for cost in costs)  # 저비용 아이템 존재
        assert any(cost >= 20 for cost in costs)  # 고비용 아이템 존재
    
    def test_default_items_cooldown_balance(self):
        """기본 아이템 쿨다운 밸런스 테스트"""
        cooldowns = [item["cooldown_seconds"] for item in DEFAULT_ITEMS]
        
        # 쿨다운 범위 확인
        assert all(cooldown > 0 for cooldown in cooldowns)
        assert any(cooldown <= 60 for cooldown in cooldowns)   # 짧은 쿨다운 아이템 존재
        assert any(cooldown >= 90 for cooldown in cooldowns)   # 긴 쿨다운 아이템 존재