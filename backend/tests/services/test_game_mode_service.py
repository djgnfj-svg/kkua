"""
게임 모드 서비스 테스트
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from services.game_mode_service import GameModeService
from models.game_mode_model import GameMode, DEFAULT_GAME_MODES
from schemas.game_mode_schema import GameModeCreate, GameModeUpdate


@pytest.fixture
def mock_db():
    """Mock 데이터베이스 세션"""
    return Mock(spec=Session)


@pytest.fixture
def game_mode_service(mock_db):
    """게임 모드 서비스 인스턴스"""
    return GameModeService(mock_db)


@pytest.fixture
def sample_game_modes():
    """테스트용 게임 모드들"""
    classic_mode = GameMode(
        mode_id=1,
        name="classic",
        display_name="클래식 모드",
        description="기본적인 끝말잇기 게임",
        turn_time_limit=30,
        max_rounds=10,
        is_active=True,
        is_default=True
    )
    
    speed_mode = GameMode(
        mode_id=2,
        name="speed",
        display_name="스피드 모드",
        description="빠른 턴 진행의 끝말잇기",
        turn_time_limit=15,
        max_rounds=15,
        is_active=True,
        is_default=False
    )
    
    inactive_mode = GameMode(
        mode_id=3,
        name="old_mode",
        display_name="구 모드",
        description="사용되지 않는 모드",
        turn_time_limit=45,
        max_rounds=8,
        is_active=False,
        is_default=False
    )
    
    return [classic_mode, speed_mode, inactive_mode]


class TestGameModeService:
    """게임 모드 서비스 테스트"""
    
    def test_initialize_default_modes_success(self, game_mode_service, mock_db):
        """기본 게임 모드 초기화 성공 테스트"""
        # Mock 설정: 기존 모드가 없음
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 테스트 실행
        result = game_mode_service.initialize_default_modes()
        
        # 검증
        assert result is True
        assert mock_db.add.call_count == len(DEFAULT_GAME_MODES)
        mock_db.commit.assert_called_once()
    
    def test_initialize_default_modes_skip_existing(self, game_mode_service, mock_db):
        """기존 모드가 있을 때 건너뛰기 테스트"""
        # Mock 설정: 첫 번째 모드는 이미 존재
        existing_mode = GameMode(name="classic")
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            existing_mode,  # 첫 번째는 존재
            None,           # 나머지는 존재하지 않음
            None
        ]
        
        # 테스트 실행
        result = game_mode_service.initialize_default_modes()
        
        # 검증
        assert result is True
        # 기존 모드를 제외하고 새로 추가됨
        assert mock_db.add.call_count == len(DEFAULT_GAME_MODES) - 1
    
    def test_initialize_default_modes_failure(self, game_mode_service, mock_db):
        """기본 게임 모드 초기화 실패 테스트"""
        # Mock 설정: 데이터베이스 오류 발생
        mock_db.query.side_effect = Exception("Database error")
        
        # 테스트 실행
        result = game_mode_service.initialize_default_modes()
        
        # 검증
        assert result is False
        mock_db.rollback.assert_called_once()
    
    def test_get_all_modes_active_only(self, game_mode_service, mock_db, sample_game_modes):
        """활성 모드만 조회 테스트"""
        classic_mode, speed_mode, inactive_mode = sample_game_modes
        
        # Mock 설정: 활성 모드만 반환
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            classic_mode, speed_mode
        ]
        
        # 테스트 실행
        result = game_mode_service.get_all_modes(active_only=True)
        
        # 검증
        assert len(result) == 2
        assert all(mode.is_active for mode in result)
        mock_db.query.assert_called_with(GameMode)
    
    def test_get_all_modes_include_inactive(self, game_mode_service, mock_db, sample_game_modes):
        """모든 모드 조회 테스트 (비활성 포함)"""
        # Mock 설정: 모든 모드 반환
        mock_db.query.return_value.order_by.return_value.all.return_value = sample_game_modes
        
        # 테스트 실행
        result = game_mode_service.get_all_modes(active_only=False)
        
        # 검증
        assert len(result) == 3
        # filter가 호출되지 않음 (활성 여부 필터링 없음)
        mock_db.query.return_value.filter.assert_not_called()
    
    def test_get_mode_by_id_success(self, game_mode_service, mock_db, sample_game_modes):
        """ID로 게임 모드 조회 성공 테스트"""
        classic_mode = sample_game_modes[0]
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.return_value = classic_mode
        
        # 테스트 실행
        result = game_mode_service.get_mode_by_id(1)
        
        # 검증
        assert result is not None
        assert result.mode_id == 1
        assert result.name == "classic"
    
    def test_get_mode_by_id_not_found(self, game_mode_service, mock_db):
        """ID로 게임 모드 조회 실패 테스트"""
        # Mock 설정: 모드 없음
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 테스트 실행
        result = game_mode_service.get_mode_by_id(999)
        
        # 검증
        assert result is None
    
    def test_get_mode_by_name_success(self, game_mode_service, mock_db, sample_game_modes):
        """이름으로 게임 모드 조회 성공 테스트"""
        speed_mode = sample_game_modes[1]
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.return_value = speed_mode
        
        # 테스트 실행
        result = game_mode_service.get_mode_by_name("speed")
        
        # 검증
        assert result is not None
        assert result.name == "speed"
        assert result.display_name == "스피드 모드"
    
    def test_get_default_mode(self, game_mode_service, mock_db, sample_game_modes):
        """기본 게임 모드 조회 테스트"""
        classic_mode = sample_game_modes[0]
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.return_value = classic_mode
        
        # 테스트 실행
        result = game_mode_service.get_default_mode()
        
        # 검증
        assert result is not None
        assert result.is_default is True
        assert result.name == "classic"
    
    def test_create_custom_mode_success(self, game_mode_service, mock_db):
        """커스텀 게임 모드 생성 성공 테스트"""
        # Mock 설정: 이름 중복 없음
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 테스트 데이터
        mode_data = GameModeCreate(
            name="custom_mode",
            display_name="커스텀 모드",
            description="사용자 정의 모드",
            turn_time_limit=25,
            max_rounds=12
        )
        
        # 테스트 실행
        result = game_mode_service.create_custom_mode(mode_data)
        
        # 검증
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_create_custom_mode_duplicate_name(self, game_mode_service, mock_db, sample_game_modes):
        """중복 이름으로 커스텀 모드 생성 실패 테스트"""
        # Mock 설정: 이름 중복
        mock_db.query.return_value.filter.return_value.first.return_value = sample_game_modes[0]
        
        # 테스트 데이터
        mode_data = GameModeCreate(
            name="classic",  # 중복된 이름
            display_name="새 클래식",
            description="중복 테스트"
        )
        
        # 테스트 실행
        result = game_mode_service.create_custom_mode(mode_data)
        
        # 검증
        assert result is None
        mock_db.add.assert_not_called()
    
    def test_update_mode_success(self, game_mode_service, mock_db, sample_game_modes):
        """게임 모드 업데이트 성공 테스트"""
        mode_to_update = sample_game_modes[1]  # speed_mode
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.return_value = mode_to_update
        
        # 테스트 데이터
        update_data = GameModeUpdate(
            display_name="슈퍼 스피드 모드",
            description="더욱 빨라진 끝말잇기",
            turn_time_limit=10
        )
        
        # 테스트 실행
        result = game_mode_service.update_mode(2, update_data)
        
        # 검증
        assert result is not None
        assert mode_to_update.display_name == "슈퍼 스피드 모드"
        assert mode_to_update.turn_time_limit == 10
        mock_db.commit.assert_called_once()
    
    def test_update_mode_not_found(self, game_mode_service, mock_db):
        """존재하지 않는 모드 업데이트 테스트"""
        # Mock 설정: 모드 없음
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 테스트 데이터
        update_data = GameModeUpdate(display_name="새 이름")
        
        # 테스트 실행
        result = game_mode_service.update_mode(999, update_data)
        
        # 검증
        assert result is None
        mock_db.commit.assert_not_called()
    
    def test_toggle_mode_status_activate(self, game_mode_service, mock_db, sample_game_modes):
        """게임 모드 활성화 테스트"""
        inactive_mode = sample_game_modes[2]  # inactive_mode
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.return_value = inactive_mode
        
        # 테스트 실행
        result = game_mode_service.toggle_mode_status(3)
        
        # 검증
        assert result is True
        assert inactive_mode.is_active is True
        mock_db.commit.assert_called_once()
    
    def test_toggle_mode_status_deactivate(self, game_mode_service, mock_db, sample_game_modes):
        """게임 모드 비활성화 테스트"""
        active_mode = sample_game_modes[1]  # speed_mode
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.return_value = active_mode
        
        # 테스트 실행
        result = game_mode_service.toggle_mode_status(2)
        
        # 검증
        assert result is True
        assert active_mode.is_active is False
        mock_db.commit.assert_called_once()
    
    def test_validate_mode_for_room_success(self, game_mode_service, mock_db, sample_game_modes):
        """게임방용 모드 검증 성공 테스트"""
        classic_mode = sample_game_modes[0]
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.return_value = classic_mode
        
        # 테스트 실행
        result = game_mode_service.validate_mode_for_room("classic", 4)
        
        # 검증
        assert result.is_valid is True
        assert result.mode_info is not None
        assert result.mode_info.name == "classic"
    
    def test_validate_mode_for_room_not_found(self, game_mode_service, mock_db):
        """존재하지 않는 모드 검증 테스트"""
        # Mock 설정: 모드 없음
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 테스트 실행
        result = game_mode_service.validate_mode_for_room("nonexistent", 4)
        
        # 검증
        assert result.is_valid is False
        assert "존재하지 않는" in result.error_message
    
    def test_validate_mode_for_room_inactive(self, game_mode_service, mock_db, sample_game_modes):
        """비활성 모드 검증 테스트"""
        inactive_mode = sample_game_modes[2]
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.return_value = inactive_mode
        
        # 테스트 실행
        result = game_mode_service.validate_mode_for_room("old_mode", 4)
        
        # 검증
        assert result.is_valid is False
        assert "비활성화된" in result.error_message
    
    def test_get_mode_settings_for_game(self, game_mode_service, mock_db, sample_game_modes):
        """게임용 모드 설정 조회 테스트"""
        speed_mode = sample_game_modes[1]
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.return_value = speed_mode
        
        # 테스트 실행
        result = game_mode_service.get_mode_settings_for_game("speed")
        
        # 검증
        assert result is not None
        assert result["turn_time_limit"] == 15
        assert result["max_rounds"] == 15
        assert result["score_multiplier"] == speed_mode.score_multiplier
        assert result["enable_advanced_scoring"] == speed_mode.enable_advanced_scoring
    
    def test_get_mode_settings_for_game_not_found(self, game_mode_service, mock_db):
        """존재하지 않는 모드의 설정 조회 테스트"""
        # Mock 설정: 모드 없음
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 테스트 실행
        result = game_mode_service.get_mode_settings_for_game("nonexistent")
        
        # 검증
        assert result is None
    
    def test_get_popular_modes(self, game_mode_service, mock_db):
        """인기 모드 조회 테스트"""
        # Mock 설정: 사용 통계가 있는 모드들
        popular_modes = [
            {"mode_name": "classic", "usage_count": 150, "avg_rating": 4.5},
            {"mode_name": "speed", "usage_count": 120, "avg_rating": 4.2},
            {"mode_name": "item", "usage_count": 80, "avg_rating": 4.0}
        ]
        
        # Mock 쿼리 결과
        mock_db.execute.return_value.fetchall.return_value = popular_modes
        
        # 테스트 실행
        result = game_mode_service.get_popular_modes(limit=3)
        
        # 검증
        assert len(result) == 3
        assert result[0]["mode_name"] == "classic"
        assert result[0]["usage_count"] == 150
    
    def test_delete_custom_mode_success(self, game_mode_service, mock_db):
        """커스텀 모드 삭제 성공 테스트"""
        custom_mode = GameMode(
            mode_id=4,
            name="custom_test",
            display_name="커스텀 테스트",
            is_active=True,
            is_default=False  # 기본 모드가 아님
        )
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.return_value = custom_mode
        
        # 테스트 실행
        result = game_mode_service.delete_custom_mode(4)
        
        # 검증
        assert result is True
        mock_db.delete.assert_called_once_with(custom_mode)
        mock_db.commit.assert_called_once()
    
    def test_delete_custom_mode_default_mode(self, game_mode_service, mock_db, sample_game_modes):
        """기본 모드 삭제 시도 테스트"""
        default_mode = sample_game_modes[0]  # is_default=True
        
        # Mock 설정
        mock_db.query.return_value.filter.return_value.first.return_value = default_mode
        
        # 테스트 실행
        result = game_mode_service.delete_custom_mode(1)
        
        # 검증
        assert result is False
        mock_db.delete.assert_not_called()
    
    def test_search_modes(self, game_mode_service, mock_db, sample_game_modes):
        """게임 모드 검색 테스트"""
        # Mock 설정: 검색 결과
        search_results = [sample_game_modes[0]]  # classic 모드만
        mock_db.query.return_value.filter.return_value.all.return_value = search_results
        
        # 테스트 실행
        result = game_mode_service.search_modes("클래식")
        
        # 검증
        assert len(result) == 1
        assert result[0].name == "classic"