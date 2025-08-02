"""
플레이어 프로필 리포지토리 테스트
"""

import pytest
from datetime import datetime, timedelta
from repositories.player_profile_repository import PlayerProfileRepository
from models.player_profile_model import PlayerProfile
from models.guest_model import Guest


@pytest.fixture
def profile_repository(db_session):
    """플레이어 프로필 리포지토리 인스턴스"""
    return PlayerProfileRepository(db_session)


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
def sample_guests(db_session):
    """테스트용 여러 게스트 사용자들"""
    guests = []
    for i in range(5):
        guest = Guest(
            uuid=f"test-uuid-{i+1}",
            nickname=f"테스트유저{i+1}",
            session_token=f"token{i+1}"
        )
        db_session.add(guest)
        guests.append(guest)
    
    db_session.commit()
    
    for guest in guests:
        db_session.refresh(guest)
    
    return guests


class TestPlayerProfileRepository:
    """플레이어 프로필 리포지토리 테스트"""
    
    def test_create_profile(self, profile_repository, sample_guest):
        """프로필 생성 테스트"""
        profile = profile_repository.create_profile(
            guest_id=sample_guest.guest_id,
            display_name="새로운 플레이어",
            bio="안녕하세요!",
            level=5,
            experience_points=250
        )
        
        # 검증
        assert profile.profile_id is not None
        assert profile.guest_id == sample_guest.guest_id
        assert profile.display_name == "새로운 플레이어"
        assert profile.bio == "안녕하세요!"
        assert profile.level == 5
        assert profile.experience_points == 250
        assert profile.created_at is not None
    
    def test_create_profile_with_defaults(self, profile_repository, sample_guest):
        """기본값으로 프로필 생성 테스트"""
        profile = profile_repository.create_profile(guest_id=sample_guest.guest_id)
        
        # 기본값 확인
        assert profile.level == 1
        assert profile.experience_points == 0
        assert profile.total_games_played == 0
        assert profile.rank_points == 1000
        assert profile.is_public is True
    
    def test_find_by_guest_id(self, profile_repository, sample_guest):
        """게스트 ID로 프로필 조회 테스트"""
        # 프로필 생성
        created_profile = profile_repository.create_profile(
            guest_id=sample_guest.guest_id,
            display_name="찾기 테스트"
        )
        
        # 조회
        found_profile = profile_repository.find_by_guest_id(sample_guest.guest_id)
        
        # 검증
        assert found_profile is not None
        assert found_profile.profile_id == created_profile.profile_id
        assert found_profile.display_name == "찾기 테스트"
        assert found_profile.guest is not None  # joinedload 확인
        assert found_profile.guest.guest_id == sample_guest.guest_id
    
    def test_find_by_guest_id_not_found(self, profile_repository):
        """존재하지 않는 게스트 ID로 조회 테스트"""
        profile = profile_repository.find_by_guest_id(999)
        assert profile is None
    
    def test_find_by_id(self, profile_repository, sample_guest):
        """프로필 ID로 조회 테스트"""
        # 프로필 생성
        created_profile = profile_repository.create_profile(
            guest_id=sample_guest.guest_id,
            display_name="ID 조회 테스트"
        )
        
        # ID로 조회
        found_profile = profile_repository.find_by_id(created_profile.profile_id)
        
        # 검증
        assert found_profile is not None
        assert found_profile.profile_id == created_profile.profile_id
        assert found_profile.display_name == "ID 조회 테스트"
    
    def test_update_profile(self, profile_repository, sample_guest):
        """프로필 업데이트 테스트"""
        # 프로필 생성
        profile = profile_repository.create_profile(
            guest_id=sample_guest.guest_id,
            display_name="원래 이름",
            bio="원래 소개"
        )
        
        original_updated_at = profile.updated_at
        
        # 업데이트
        update_data = {
            "display_name": "변경된 이름",
            "bio": "변경된 소개",
            "level": 10,
            "experience_points": 500
        }
        
        updated_profile = profile_repository.update_profile(sample_guest.guest_id, update_data)
        
        # 검증
        assert updated_profile is not None
        assert updated_profile.display_name == "변경된 이름"
        assert updated_profile.bio == "변경된 소개"
        assert updated_profile.level == 10
        assert updated_profile.experience_points == 500
        assert updated_profile.updated_at > original_updated_at
    
    def test_update_profile_partial(self, profile_repository, sample_guest):
        """부분 업데이트 테스트"""
        # 프로필 생성
        profile = profile_repository.create_profile(
            guest_id=sample_guest.guest_id,
            display_name="원래 이름",
            bio="원래 소개",
            level=1
        )
        
        # 일부 필드만 업데이트
        update_data = {"display_name": "새 이름"}
        updated_profile = profile_repository.update_profile(sample_guest.guest_id, update_data)
        
        # 변경된 필드와 유지된 필드 확인
        assert updated_profile.display_name == "새 이름"
        assert updated_profile.bio == "원래 소개"  # 변경되지 않음
        assert updated_profile.level == 1         # 변경되지 않음
    
    def test_update_profile_none_values(self, profile_repository, sample_guest):
        """None 값 업데이트 테스트"""
        # 프로필 생성
        profile = profile_repository.create_profile(
            guest_id=sample_guest.guest_id,
            display_name="원래 이름"
        )
        
        # None 값들을 포함한 업데이트 (None은 무시되어야 함)
        update_data = {
            "display_name": "새 이름",
            "bio": None,  # 무시되어야 함
            "level": 5
        }
        
        updated_profile = profile_repository.update_profile(sample_guest.guest_id, update_data)
        
        assert updated_profile.display_name == "새 이름"
        assert updated_profile.level == 5
        # bio는 None이므로 원래 값 유지
    
    def test_update_profile_not_found(self, profile_repository):
        """존재하지 않는 프로필 업데이트 테스트"""
        result = profile_repository.update_profile(999, {"display_name": "테스트"})
        assert result is None
    
    def test_get_or_create_profile_existing(self, profile_repository, sample_guest):
        """기존 프로필 조회 테스트"""
        # 프로필 미리 생성
        existing_profile = profile_repository.create_profile(
            guest_id=sample_guest.guest_id,
            display_name="기존 프로필"
        )
        
        # get_or_create 호출
        profile = profile_repository.get_or_create_profile(sample_guest.guest_id)
        
        # 기존 프로필이 반환되어야 함
        assert profile.profile_id == existing_profile.profile_id
        assert profile.display_name == "기존 프로필"
    
    def test_get_or_create_profile_new(self, profile_repository, sample_guest):
        """새 프로필 생성 테스트"""
        # 프로필이 없는 상태에서 get_or_create 호출
        profile = profile_repository.get_or_create_profile(sample_guest.guest_id)
        
        # 새 프로필이 생성되어야 함
        assert profile.profile_id is not None
        assert profile.guest_id == sample_guest.guest_id
        assert profile.level == 1  # 기본값
        assert profile.experience_points == 0  # 기본값
    
    def test_get_top_players_by_rank(self, profile_repository, sample_guests):
        """랭킹 순위별 상위 플레이어 조회 테스트"""
        # 여러 프로필 생성 (다양한 랭킹 포인트)
        rank_points = [2500, 1800, 1500, 1200, 900]
        profiles = []
        
        for i, guest in enumerate(sample_guests):
            profile = profile_repository.create_profile(
                guest_id=guest.guest_id,
                display_name=f"플레이어{i+1}",
                rank_points=rank_points[i]
            )
            profiles.append(profile)
        
        # 상위 3명 조회
        top_players = profile_repository.get_top_players_by_rank(limit=3)
        
        # 검증: 랭킹 포인트 순으로 정렬되어야 함
        assert len(top_players) == 3
        assert top_players[0].rank_points == 2500
        assert top_players[1].rank_points == 1800
        assert top_players[2].rank_points == 1500
    
    def test_get_top_players_by_level(self, profile_repository, sample_guests):
        """레벨별 상위 플레이어 조회 테스트"""
        # 여러 프로필 생성 (다양한 레벨)
        levels = [50, 35, 28, 15, 8]
        
        for i, guest in enumerate(sample_guests):
            profile_repository.create_profile(
                guest_id=guest.guest_id,
                display_name=f"플레이어{i+1}",
                level=levels[i]
            )
        
        # 상위 3명 조회
        top_players = profile_repository.get_top_players_by_level(limit=3)
        
        # 검증: 레벨 순으로 정렬되어야 함
        assert len(top_players) == 3
        assert top_players[0].level == 50
        assert top_players[1].level == 35
        assert top_players[2].level == 28
    
    def test_search_profiles_by_nickname(self, profile_repository, sample_guests):
        """닉네임으로 프로필 검색 테스트"""
        # 프로필 생성
        for i, guest in enumerate(sample_guests):
            profile_repository.create_profile(
                guest_id=guest.guest_id,
                display_name=f"검색플레이어{i+1}"
            )
        
        # 검색
        results = profile_repository.search_profiles("검색플레이어")
        
        # 검증
        assert len(results) == 5
        for profile in results:
            assert "검색플레이어" in profile.display_name
    
    def test_get_player_ranking(self, profile_repository, sample_guests):
        """플레이어 순위 조회 테스트"""
        # 랭킹 포인트가 다른 프로필들 생성
        rank_points = [2000, 1800, 1600, 1400, 1200]
        
        for i, guest in enumerate(sample_guests):
            profile_repository.create_profile(
                guest_id=guest.guest_id,
                rank_points=rank_points[i]
            )
        
        # 3번째 플레이어 (1600 포인트)의 순위 조회
        ranking_info = profile_repository.get_player_ranking(sample_guests[2].guest_id)
        
        # 검증
        assert ranking_info["global_rank"] == 3  # 3위
        assert ranking_info["rank_points"] == 1600
        assert ranking_info["total_players"] == 5
    
    def test_get_level_distribution(self, profile_repository, sample_guests):
        """레벨 분포 조회 테스트"""
        # 다양한 레벨의 프로필들 생성
        levels = [5, 15, 25, 35, 45]
        
        for i, guest in enumerate(sample_guests):
            profile_repository.create_profile(
                guest_id=guest.guest_id,
                level=levels[i]
            )
        
        # 레벨 분포 조회
        distribution = profile_repository.get_level_distribution()
        
        # 검증
        assert len(distribution) > 0
        # 각 레벨 구간별 플레이어 수가 계산되어야 함
        total_players = sum(bucket["player_count"] for bucket in distribution)
        assert total_players == 5
    
    def test_get_recent_achievements(self, profile_repository, sample_guest):
        """최근 업적 조회 테스트"""
        # 업적이 있는 프로필 생성
        achievements = [
            {
                "id": "first_win",
                "name": "첫 승리",
                "earned_at": datetime.utcnow().isoformat()
            },
            {
                "id": "streak_5",
                "name": "5연승",
                "earned_at": (datetime.utcnow() - timedelta(days=1)).isoformat()
            }
        ]
        
        profile = profile_repository.create_profile(
            guest_id=sample_guest.guest_id,
            achievements=achievements
        )
        
        # 최근 업적 조회
        recent_achievements = profile_repository.get_recent_achievements(
            sample_guest.guest_id, 
            days=7
        )
        
        # 검증
        assert len(recent_achievements) == 2
        assert recent_achievements[0]["id"] == "first_win"
    
    def test_update_game_statistics(self, profile_repository, sample_guest):
        """게임 통계 업데이트 테스트"""
        # 프로필 생성
        profile = profile_repository.create_profile(guest_id=sample_guest.guest_id)
        
        # 게임 통계 데이터
        game_stats = {
            "won": True,
            "words_submitted": 5,
            "score": 120,
            "avg_response_time": 3.5,
            "longest_word": "프로그래밍"
        }
        
        # 통계 업데이트
        updated_profile = profile_repository.update_game_statistics(
            sample_guest.guest_id, 
            game_stats
        )
        
        # 검증
        assert updated_profile.total_games_played == 1
        assert updated_profile.total_games_won == 1
        assert updated_profile.total_words_submitted == 5
        assert updated_profile.total_score == 120
        assert updated_profile.longest_word == "프로그래밍"
        assert updated_profile.current_streak == 1
    
    def test_add_experience_and_level_up(self, profile_repository, sample_guest):
        """경험치 추가 및 레벨업 테스트"""
        # 프로필 생성
        profile = profile_repository.create_profile(
            guest_id=sample_guest.guest_id,
            experience_points=80  # 레벨업에 20 부족
        )
        
        # 경험치 추가 (레벨업 발생)
        updated_profile = profile_repository.add_experience(sample_guest.guest_id, 50)
        
        # 검증
        assert updated_profile.level == 2  # 레벨업
        assert updated_profile.experience_points == 30  # 50 - 20 = 30
        assert updated_profile.experience_to_next_level == 150  # 레벨 2->3
    
    def test_get_public_profiles_only(self, profile_repository, sample_guests):
        """공개 프로필만 조회 테스트"""
        # 공개/비공개 프로필 생성
        for i, guest in enumerate(sample_guests):
            is_public = i % 2 == 0  # 짝수 인덱스만 공개
            profile_repository.create_profile(
                guest_id=guest.guest_id,
                display_name=f"플레이어{i+1}",
                is_public=is_public
            )
        
        # 공개 프로필만 조회
        public_profiles = profile_repository.get_public_profiles(limit=10)
        
        # 검증: 모든 결과가 공개 프로필이어야 함
        assert all(profile.is_public for profile in public_profiles)
        assert len(public_profiles) == 3  # 5명 중 3명이 공개 (0, 2, 4번째)
    
    def test_get_profile_with_rank_tier(self, profile_repository, sample_guest):
        """랭킹 티어가 포함된 프로필 조회 테스트"""
        # 다이아몬드 티어 프로필 생성
        profile = profile_repository.create_profile(
            guest_id=sample_guest.guest_id,
            rank_points=2500  # 다이아몬드 티어
        )
        
        # 프로필 조회
        found_profile = profile_repository.find_by_guest_id(sample_guest.guest_id)
        
        # 검증: rank_tier 프로퍼티 확인
        assert found_profile.rank_tier == "diamond"
        assert found_profile.rank_points == 2500