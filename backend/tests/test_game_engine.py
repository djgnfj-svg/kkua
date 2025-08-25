import pytest
import asyncio
from services.game_engine import GameEngine
from models.game_models import GameRoom, Player

@pytest.mark.asyncio
class TestGameEngine:
    async def setup_method(self):
        self.engine = GameEngine()
    
    async def test_create_room(self):
        """게임룸 생성 테스트"""
        room = await self.engine.create_room(
            host_id=1,
            room_name="테스트룸",
            max_players=4
        )
        assert room is not None
        assert room.room_name == "테스트룸"
        assert room.max_players == 4
    
    async def test_join_room(self):
        """게임룸 참가 테스트"""
        room = await self.engine.create_room(1, "테스트룸", 4)
        
        # 정상 참가
        success = await self.engine.join_room(room.id, 2)
        assert success == True
        
        # 중복 참가
        success = await self.engine.join_room(room.id, 2)
        assert success == False
    
    async def test_start_game_conditions(self):
        """게임 시작 조건 테스트"""
        room = await self.engine.create_room(1, "테스트룸", 4)
        
        # 혼자서는 시작 불가
        can_start = await self.engine.can_start_game(room.id)
        assert can_start == False
        
        # 2명 이상이면 시작 가능
        await self.engine.join_room(room.id, 2)
        can_start = await self.engine.can_start_game(room.id)
        assert can_start == True