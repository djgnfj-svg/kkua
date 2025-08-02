"""
게임 모드 모델 테스트
"""

import pytest
from models.game_mode_model import GameMode, DEFAULT_GAME_MODES


class TestGameModeModel:
    """게임 모드 모델 테스트"""
    
    def test_create_game_mode(self, db_session):
        """게임 모드 생성 테스트"""
        game_mode = GameMode(
            name="test_mode",
            display_name="테스트 모드",
            description="테스트용 게임 모드입니다",
            turn_time_limit=45,
            max_rounds=15,
            min_word_length=3,
            max_word_length=8,
            score_multiplier=1.5,
            enable_advanced_scoring=True,
            special_rules={"allow_items": True, "bonus_time": 10},
            is_active=True,
            is_default=False
        )
        
        db_session.add(game_mode)
        db_session.commit()
        db_session.refresh(game_mode)
        
        assert game_mode.mode_id is not None
        assert game_mode.name == "test_mode"
        assert game_mode.display_name == "테스트 모드"
        assert game_mode.description == "테스트용 게임 모드입니다"
        assert game_mode.turn_time_limit == 45
        assert game_mode.max_rounds == 15
        assert game_mode.min_word_length == 3
        assert game_mode.max_word_length == 8
        assert game_mode.score_multiplier == 1.5
        assert game_mode.enable_advanced_scoring is True
        assert game_mode.special_rules == {"allow_items": True, "bonus_time": 10}
        assert game_mode.is_active is True
        assert game_mode.is_default is False
        assert game_mode.created_at is not None
        assert game_mode.updated_at is not None
    
    def test_game_mode_defaults(self, db_session):
        """게임 모드 기본값 테스트"""
        game_mode = GameMode(
            name="minimal_mode",
            display_name="최소 모드"
        )
        
        db_session.add(game_mode)
        db_session.commit()
        db_session.refresh(game_mode)
        
        # 기본값 확인
        assert game_mode.turn_time_limit == 30
        assert game_mode.max_rounds == 10
        assert game_mode.min_word_length == 2
        assert game_mode.max_word_length == 10
        assert game_mode.score_multiplier == 1.0
        assert game_mode.enable_advanced_scoring is True
        assert game_mode.special_rules == {}
        assert game_mode.is_active is True
        assert game_mode.is_default is False
    
    def test_game_mode_unique_name(self, db_session):
        """게임 모드 이름 고유성 테스트"""
        # 첫 번째 게임 모드
        game_mode1 = GameMode(
            name="unique_mode",
            display_name="유니크 모드 1"
        )
        db_session.add(game_mode1)
        db_session.commit()
        
        # 같은 이름의 두 번째 게임 모드
        game_mode2 = GameMode(
            name="unique_mode",
            display_name="유니크 모드 2"
        )
        db_session.add(game_mode2)
        
        with pytest.raises(Exception):  # IntegrityError 예상
            db_session.commit()
    
    def test_game_mode_json_special_rules(self, db_session):
        """특수 규칙 JSON 필드 테스트"""
        complex_rules = {
            "items_enabled": True,
            "power_ups": ["speed_boost", "double_score"],
            "special_events": {
                "sudden_death": {"enabled": True, "trigger_round": 8},
                "time_pressure": {"enabled": False}
            },
            "scoring": {
                "base_multiplier": 1.2,
                "bonus_conditions": ["speed", "word_length", "creativity"]
            }
        }
        
        game_mode = GameMode(
            name="complex_mode",
            display_name="복잡한 모드",
            special_rules=complex_rules
        )
        
        db_session.add(game_mode)
        db_session.commit()
        db_session.refresh(game_mode)
        
        assert game_mode.special_rules == complex_rules
        assert game_mode.special_rules["items_enabled"] is True
        assert len(game_mode.special_rules["power_ups"]) == 2
        assert game_mode.special_rules["special_events"]["sudden_death"]["trigger_round"] == 8
    
    def test_game_mode_active_inactive(self, db_session):
        """게임 모드 활성/비활성 테스트"""
        # 활성 모드
        active_mode = GameMode(
            name="active_mode",
            display_name="활성 모드",
            is_active=True
        )
        
        # 비활성 모드
        inactive_mode = GameMode(
            name="inactive_mode",
            display_name="비활성 모드",
            is_active=False
        )
        
        db_session.add_all([active_mode, inactive_mode])
        db_session.commit()
        
        # 활성 모드만 조회
        active_modes = db_session.query(GameMode).filter(GameMode.is_active == True).all()
        assert len(active_modes) == 1
        assert active_modes[0].name == "active_mode"
        
        # 모든 모드 조회
        all_modes = db_session.query(GameMode).all()
        assert len(all_modes) == 2
    
    def test_game_mode_default_flag(self, db_session):
        """기본 게임 모드 플래그 테스트"""
        # 기본 모드
        default_mode = GameMode(
            name="default_mode",
            display_name="기본 모드",
            is_default=True
        )
        
        # 일반 모드
        normal_mode = GameMode(
            name="normal_mode",
            display_name="일반 모드",
            is_default=False
        )
        
        db_session.add_all([default_mode, normal_mode])
        db_session.commit()
        
        # 기본 모드 조회
        default_modes = db_session.query(GameMode).filter(GameMode.is_default == True).all()
        assert len(default_modes) == 1
        assert default_modes[0].name == "default_mode"
    
    def test_game_mode_time_limits(self, db_session):
        """시간 제한 설정 테스트"""
        # 빠른 모드
        speed_mode = GameMode(
            name="speed_mode",
            display_name="스피드 모드",
            turn_time_limit=15,
            max_rounds=20
        )
        
        # 느린 모드
        slow_mode = GameMode(
            name="slow_mode",
            display_name="여유 모드",
            turn_time_limit=60,
            max_rounds=5
        )
        
        db_session.add_all([speed_mode, slow_mode])
        db_session.commit()
        
        assert speed_mode.turn_time_limit == 15
        assert speed_mode.max_rounds == 20
        assert slow_mode.turn_time_limit == 60
        assert slow_mode.max_rounds == 5
    
    def test_game_mode_word_length_constraints(self, db_session):
        """단어 길이 제한 테스트"""
        game_mode = GameMode(
            name="word_length_mode",
            display_name="단어 길이 모드",
            min_word_length=4,
            max_word_length=6
        )
        
        db_session.add(game_mode)
        db_session.commit()
        db_session.refresh(game_mode)
        
        assert game_mode.min_word_length == 4
        assert game_mode.max_word_length == 6
    
    def test_game_mode_score_multiplier(self, db_session):
        """점수 배수 테스트"""
        # 하드 모드 (높은 배수)
        hard_mode = GameMode(
            name="hard_mode",
            display_name="하드 모드",
            score_multiplier=2.0
        )
        
        # 이지 모드 (낮은 배수)
        easy_mode = GameMode(
            name="easy_mode",
            display_name="이지 모드",
            score_multiplier=0.8
        )
        
        db_session.add_all([hard_mode, easy_mode])
        db_session.commit()
        
        assert hard_mode.score_multiplier == 2.0
        assert easy_mode.score_multiplier == 0.8
    
    def test_default_game_modes_structure(self):
        """기본 게임 모드 데이터 구조 테스트"""
        assert isinstance(DEFAULT_GAME_MODES, list)
        assert len(DEFAULT_GAME_MODES) > 0
        
        for mode_data in DEFAULT_GAME_MODES:
            # 필수 필드 확인
            assert "name" in mode_data
            assert "display_name" in mode_data
            assert "description" in mode_data
            
            # 설정 필드 확인
            assert "turn_time_limit" in mode_data
            assert "max_rounds" in mode_data
            assert "min_word_length" in mode_data
            assert "max_word_length" in mode_data
            
            # 타입 확인
            assert isinstance(mode_data["name"], str)
            assert isinstance(mode_data["display_name"], str)
            assert isinstance(mode_data["turn_time_limit"], int)
            assert isinstance(mode_data["max_rounds"], int)
    
    def test_game_mode_advanced_scoring_flag(self, db_session):
        """고급 점수 시스템 플래그 테스트"""
        # 고급 점수 시스템 사용
        advanced_mode = GameMode(
            name="advanced_mode",
            display_name="고급 모드",
            enable_advanced_scoring=True
        )
        
        # 기본 점수 시스템 사용
        basic_mode = GameMode(
            name="basic_mode",
            display_name="기본 모드",
            enable_advanced_scoring=False
        )
        
        db_session.add_all([advanced_mode, basic_mode])
        db_session.commit()
        
        assert advanced_mode.enable_advanced_scoring is True
        assert basic_mode.enable_advanced_scoring is False
    
    def test_game_mode_updated_at_auto_update(self, db_session):
        """updated_at 자동 업데이트 테스트"""
        game_mode = GameMode(
            name="update_test_mode",
            display_name="업데이트 테스트 모드"
        )
        
        db_session.add(game_mode)
        db_session.commit()
        db_session.refresh(game_mode)
        
        original_updated_at = game_mode.updated_at
        
        # 모드 수정
        game_mode.display_name = "수정된 테스트 모드"
        db_session.commit()
        db_session.refresh(game_mode)
        
        assert game_mode.updated_at > original_updated_at