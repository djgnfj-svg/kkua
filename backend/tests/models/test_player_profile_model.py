"""
플레이어 프로필 모델 테스트
"""

import pytest
from datetime import datetime, timedelta
from models.player_profile_model import PlayerProfile
from models.guest_model import Guest


@pytest.fixture
def sample_guest(db_session):
    """테스트용 게스트 사용자"""
    guest = Guest(
        uuid="test-uuid-profile",
        nickname="프로필테스터",
        session_token="profile_token"
    )
    db_session.add(guest)
    db_session.commit()
    db_session.refresh(guest)
    return guest


@pytest.fixture
def sample_profile(db_session, sample_guest):
    """테스트용 플레이어 프로필"""
    profile = PlayerProfile(
        guest_id=sample_guest.guest_id,
        display_name="테스트 플레이어",
        bio="테스트용 프로필입니다"
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


class TestPlayerProfileModel:
    """플레이어 프로필 모델 테스트"""
    
    def test_create_player_profile(self, db_session, sample_guest):
        """플레이어 프로필 생성 테스트"""
        profile = PlayerProfile(
            guest_id=sample_guest.guest_id,
            display_name="새로운 플레이어",
            bio="안녕하세요! 끝말잇기를 좋아합니다.",
            avatar_url="https://example.com/avatar.png",
            banner_url="https://example.com/banner.png"
        )
        
        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)
        
        assert profile.profile_id is not None
        assert profile.guest_id == sample_guest.guest_id
        assert profile.display_name == "새로운 플레이어"
        assert profile.bio == "안녕하세요! 끝말잇기를 좋아합니다."
        assert profile.avatar_url == "https://example.com/avatar.png"
        assert profile.banner_url == "https://example.com/banner.png"
        assert profile.created_at is not None
        assert profile.updated_at is not None
    
    def test_player_profile_defaults(self, db_session, sample_guest):
        """플레이어 프로필 기본값 테스트"""
        profile = PlayerProfile(guest_id=sample_guest.guest_id)
        
        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)
        
        # 게임 통계 기본값
        assert profile.total_games_played == 0
        assert profile.total_games_won == 0
        assert profile.total_games_lost == 0
        assert profile.total_words_submitted == 0
        assert profile.total_score == 0
        
        # 상세 통계 기본값
        assert profile.longest_word_length == 0
        assert profile.best_streak == 0
        assert profile.current_streak == 0
        
        # 레벨 시스템 기본값
        assert profile.level == 1
        assert profile.experience_points == 0
        assert profile.experience_to_next_level == 100
        
        # 랭킹 기본값
        assert profile.rank_points == 1000
        
        # JSON 필드 기본값
        assert profile.mode_statistics == {}
        assert profile.achievements == []
        assert profile.badges == []
        assert profile.favorite_words == []
        
        # 설정 기본값
        assert profile.preferred_game_mode == "classic"
        assert profile.is_public is True
        assert profile.allow_friend_requests is True
    
    def test_win_rate_property(self, db_session, sample_profile):
        """승률 계산 프로퍼티 테스트"""
        # 게임을 하지 않은 경우
        assert sample_profile.win_rate == 0.0
        
        # 게임 통계 설정
        sample_profile.total_games_played = 10
        sample_profile.total_games_won = 7
        sample_profile.total_games_lost = 3
        
        db_session.commit()
        db_session.refresh(sample_profile)
        
        assert sample_profile.win_rate == 70.0
    
    def test_average_score_property(self, db_session, sample_profile):
        """평균 점수 계산 프로퍼티 테스트"""
        # 게임을 하지 않은 경우
        assert sample_profile.average_score == 0.0
        
        # 게임 통계 설정
        sample_profile.total_games_played = 5
        sample_profile.total_score = 750
        
        db_session.commit()
        db_session.refresh(sample_profile)
        
        assert sample_profile.average_score == 150.0
    
    def test_rank_tier_property(self, db_session, sample_profile):
        """랭킹 티어 프로퍼티 테스트"""
        # Bronze 티어
        sample_profile.rank_points = 500
        assert sample_profile.rank_tier == "bronze"
        
        # Silver 티어
        sample_profile.rank_points = 900
        assert sample_profile.rank_tier == "silver"
        
        # Gold 티어
        sample_profile.rank_points = 1300
        assert sample_profile.rank_tier == "gold"
        
        # Platinum 티어
        sample_profile.rank_points = 1700
        assert sample_profile.rank_tier == "platinum"
        
        # Diamond 티어
        sample_profile.rank_points = 2100
        assert sample_profile.rank_tier == "diamond"
    
    def test_add_achievement(self, db_session, sample_profile):
        """업적 추가 테스트"""
        # 첫 번째 업적 추가
        sample_profile.add_achievement("first_win", "첫 승리")
        
        assert len(sample_profile.achievements) == 1
        achievement = sample_profile.achievements[0]
        assert achievement["id"] == "first_win"
        assert achievement["name"] == "첫 승리"
        assert "earned_at" in achievement
        
        # 두 번째 업적 추가
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        sample_profile.add_achievement("word_master", "단어 마스터", custom_time)
        
        assert len(sample_profile.achievements) == 2
        second_achievement = sample_profile.achievements[1]
        assert second_achievement["id"] == "word_master"
        assert second_achievement["name"] == "단어 마스터"
        
        # 중복 업적 추가 시도
        sample_profile.add_achievement("first_win", "첫 승리 중복")
        assert len(sample_profile.achievements) == 2  # 중복되므로 추가되지 않음
    
    def test_add_badge(self, db_session, sample_profile):
        """배지 추가 테스트"""
        # 첫 번째 배지 추가
        sample_profile.add_badge("newbie", "새내기", "starter")
        
        assert len(sample_profile.badges) == 1
        badge = sample_profile.badges[0]
        assert badge["id"] == "newbie"
        assert badge["name"] == "새내기"
        assert badge["type"] == "starter"
        assert "earned_at" in badge
        
        # 두 번째 배지 추가
        sample_profile.add_badge("veteran", "베테랑", "experience")
        
        assert len(sample_profile.badges) == 2
        
        # 중복 배지 추가 시도
        sample_profile.add_badge("newbie", "새내기 중복", "starter")
        assert len(sample_profile.badges) == 2  # 중복되므로 추가되지 않음
    
    def test_update_game_statistics_win(self, db_session, sample_profile):
        """게임 통계 업데이트 테스트 (승리)"""
        game_result = {
            "won": True,
            "words_submitted": 5,
            "score": 120,
            "avg_response_time": 3.5,
            "longest_word": "안녕하세요"
        }
        
        sample_profile.update_game_statistics(game_result)
        
        assert sample_profile.total_games_played == 1
        assert sample_profile.total_games_won == 1
        assert sample_profile.total_games_lost == 0
        assert sample_profile.total_words_submitted == 5
        assert sample_profile.total_score == 120
        assert sample_profile.current_streak == 1
        assert sample_profile.best_streak == 1
        assert sample_profile.fastest_response_time == 3.5
        assert sample_profile.average_response_time == 3.5
        assert sample_profile.longest_word == "안녕하세요"
        assert sample_profile.longest_word_length == 5
        assert sample_profile.last_game_at is not None
        assert sample_profile.first_game_at is not None
    
    def test_update_game_statistics_loss(self, db_session, sample_profile):
        """게임 통계 업데이트 테스트 (패배)"""
        # 먼저 연승 기록을 만들어둠
        sample_profile.current_streak = 3
        sample_profile.best_streak = 3
        
        game_result = {
            "won": False,
            "words_submitted": 3,
            "score": 45,
            "avg_response_time": 5.2,
            "longest_word": "게임"
        }
        
        sample_profile.update_game_statistics(game_result)
        
        assert sample_profile.total_games_played == 1
        assert sample_profile.total_games_won == 0
        assert sample_profile.total_games_lost == 1
        assert sample_profile.current_streak == 0  # 패배로 연승 중단
        assert sample_profile.best_streak == 3     # 최고 연승은 유지
    
    def test_add_experience_and_level_up(self, db_session, sample_profile):
        """경험치 추가 및 레벨업 테스트"""
        initial_level = sample_profile.level
        initial_exp = sample_profile.experience_points
        
        # 50 경험치 추가 (레벨업 안됨)
        sample_profile.add_experience(50)
        
        assert sample_profile.level == initial_level
        assert sample_profile.experience_points == initial_exp + 50
        
        # 60 경험치 더 추가 (총 110, 레벨업 됨)
        sample_profile.add_experience(60)
        
        assert sample_profile.level == initial_level + 1
        assert sample_profile.experience_points == 10  # 100을 넘어서 10이 남음
        assert sample_profile.experience_to_next_level == 150  # 레벨 2에서 3으로 가는 경험치
    
    def test_calculate_experience_from_game(self, db_session, sample_profile):
        """게임 결과에 따른 경험치 계산 테스트"""
        # 승리한 게임
        win_result = {
            "won": True,
            "score": 150,
            "words_submitted": 5
        }
        
        win_exp = sample_profile._calculate_experience(win_result)
        expected_win_exp = 10 + 20 + 15  # 기본(10) + 승리보너스(20) + 점수(150//10=15)
        assert win_exp == expected_win_exp
        
        # 패배한 게임
        loss_result = {
            "won": False,
            "score": 80,
            "words_submitted": 3
        }
        
        loss_exp = sample_profile._calculate_experience(loss_result)
        expected_loss_exp = 10 + 8  # 기본(10) + 점수(80//10=8)
        assert loss_exp == expected_loss_exp
    
    def test_multiple_level_ups(self, db_session, sample_profile):
        """여러 레벨 동시 업 테스트"""
        # 대량의 경험치 추가 (여러 레벨업 발생)
        sample_profile.add_experience(500)
        
        # 레벨 1에서 시작해서 여러 레벨 올라감
        # 레벨 1->2: 100exp, 레벨 2->3: 150exp, 레벨 3->4: 200exp
        # 총 450exp 필요, 50exp 남음
        assert sample_profile.level == 4
        assert sample_profile.experience_points == 50
        assert sample_profile.experience_to_next_level == 250  # 레벨 4->5
    
    def test_profile_relationship_with_guest(self, db_session, sample_guest, sample_profile):
        """프로필과 게스트 관계 테스트"""
        # 프로필에서 게스트 접근
        assert sample_profile.guest is not None
        assert sample_profile.guest.guest_id == sample_guest.guest_id
        assert sample_profile.guest.nickname == "프로필테스터"
        
        # 게스트에서 프로필 접근 (backref)
        assert sample_guest.profile is not None
        assert sample_guest.profile.profile_id == sample_profile.profile_id
    
    def test_profile_privacy_settings(self, db_session, sample_profile):
        """프로필 프라이버시 설정 테스트"""
        # 공개 프로필
        sample_profile.is_public = True
        sample_profile.allow_friend_requests = True
        
        assert sample_profile.is_public is True
        assert sample_profile.allow_friend_requests is True
        
        # 비공개 프로필
        sample_profile.is_public = False
        sample_profile.allow_friend_requests = False
        
        assert sample_profile.is_public is False
        assert sample_profile.allow_friend_requests is False
    
    def test_favorite_words_management(self, db_session, sample_profile):
        """즐겨 사용하는 단어 관리 테스트"""
        # 즐겨 사용하는 단어 추가
        favorite_words = ["사과", "바나나", "컴퓨터", "프로그래밍"]
        sample_profile.favorite_words = favorite_words
        
        db_session.commit()
        db_session.refresh(sample_profile)
        
        assert len(sample_profile.favorite_words) == 4
        assert "사과" in sample_profile.favorite_words
        assert "프로그래밍" in sample_profile.favorite_words
    
    def test_mode_statistics_tracking(self, db_session, sample_profile):
        """게임 모드별 통계 추적 테스트"""
        mode_stats = {
            "classic": {
                "games_played": 15,
                "games_won": 12,
                "total_score": 1800,
                "avg_score": 120.0
            },
            "speed": {
                "games_played": 8,
                "games_won": 5,
                "total_score": 640,
                "avg_score": 80.0
            }
        }
        
        sample_profile.mode_statistics = mode_stats
        
        db_session.commit()
        db_session.refresh(sample_profile)
        
        assert sample_profile.mode_statistics["classic"]["games_played"] == 15
        assert sample_profile.mode_statistics["speed"]["games_won"] == 5
    
    def test_response_time_statistics(self, db_session, sample_profile):
        """응답 시간 통계 테스트"""
        # 첫 번째 게임
        game1 = {
            "won": True,
            "avg_response_time": 4.0,
            "words_submitted": 3,
            "score": 90
        }
        sample_profile.update_game_statistics(game1)
        
        assert sample_profile.fastest_response_time == 4.0
        assert sample_profile.average_response_time == 4.0
        
        # 두 번째 게임 (더 빠른 응답)
        game2 = {
            "won": False,
            "avg_response_time": 2.5,
            "words_submitted": 2,
            "score": 30
        }
        sample_profile.update_game_statistics(game2)
        
        assert sample_profile.fastest_response_time == 2.5
        # 평균 응답 시간: (4.0 + 2.5) / 2 = 3.25
        assert abs(sample_profile.average_response_time - 3.25) < 0.01
    
    def test_longest_word_tracking(self, db_session, sample_profile):
        """가장 긴 단어 추적 테스트"""
        # 첫 번째 게임
        game1 = {
            "won": True,
            "longest_word": "컴퓨터",
            "words_submitted": 3,
            "score": 90
        }
        sample_profile.update_game_statistics(game1)
        
        assert sample_profile.longest_word == "컴퓨터"
        assert sample_profile.longest_word_length == 3
        
        # 두 번째 게임 (더 긴 단어)
        game2 = {
            "won": True,
            "longest_word": "프로그래밍",
            "words_submitted": 4,
            "score": 120
        }
        sample_profile.update_game_statistics(game2)
        
        assert sample_profile.longest_word == "프로그래밍"
        assert sample_profile.longest_word_length == 5
        
        # 세 번째 게임 (더 짧은 단어)
        game3 = {
            "won": True,
            "longest_word": "사과",
            "words_submitted": 2,
            "score": 60
        }
        sample_profile.update_game_statistics(game3)
        
        # 가장 긴 단어는 변경되지 않음
        assert sample_profile.longest_word == "프로그래밍"
        assert sample_profile.longest_word_length == 5
    
    def test_profile_repr(self, db_session, sample_profile):
        """프로필 __repr__ 테스트"""
        repr_str = repr(sample_profile)
        assert str(sample_profile.guest_id) in repr_str
        assert str(sample_profile.level) in repr_str
        assert str(sample_profile.rank_points) in repr_str
    
    def test_profile_unique_guest_constraint(self, db_session, sample_guest):
        """게스트당 하나의 프로필만 가능한 제약 테스트"""
        # 첫 번째 프로필 생성
        profile1 = PlayerProfile(guest_id=sample_guest.guest_id)
        db_session.add(profile1)
        db_session.commit()
        
        # 같은 게스트에 대한 두 번째 프로필 생성 시도
        profile2 = PlayerProfile(guest_id=sample_guest.guest_id)
        db_session.add(profile2)
        
        with pytest.raises(Exception):  # IntegrityError 예상
            db_session.commit()
    
    def test_profile_activity_tracking(self, db_session, sample_profile):
        """활동 추적 테스트"""
        # 첫 게임 시간 설정
        first_game_time = datetime.utcnow() - timedelta(days=30)
        sample_profile.first_game_at = first_game_time
        sample_profile.total_play_time = 3600  # 1시간
        
        db_session.commit()
        db_session.refresh(sample_profile)
        
        assert sample_profile.first_game_at == first_game_time
        assert sample_profile.total_play_time == 3600
        
        # 새 게임 통계 업데이트 시 last_game_at만 변경됨
        game_result = {"won": True, "words_submitted": 2, "score": 50}
        sample_profile.update_game_statistics(game_result)
        
        assert sample_profile.first_game_at == first_game_time  # 변경되지 않음
        assert sample_profile.last_game_at > first_game_time    # 새로 설정됨