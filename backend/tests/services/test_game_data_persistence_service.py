"""
GameDataPersistenceService 테스트
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from services.game_data_persistence_service import GameDataPersistenceService
from services.redis_game_service import RedisGameService
from models.game_log_model import GameLog
from models.player_game_stats_model import PlayerGameStats
from models.word_chain_entry_model import WordChainEntry
from models.guest_model import Guest
from repositories.game_log_repository import GameLogRepository


class TestGameDataPersistenceService:
    """GameDataPersistenceService 테스트 클래스"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock 데이터베이스 세션"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_redis_service(self):
        """Mock Redis 서비스"""
        return Mock(spec=RedisGameService)
    
    @pytest.fixture
    def persistence_service(self, mock_db, mock_redis_service):
        """테스트용 GameDataPersistenceService 인스턴스"""
        service = GameDataPersistenceService(mock_db, mock_redis_service)
        service.game_log_repository = Mock(spec=GameLogRepository)
        return service
    
    @pytest.fixture
    def sample_game_state(self):
        """샘플 게임 상태 데이터"""
        return {
            'room_id': 100,
            'participants': [
                {'guest_id': 1, 'nickname': '플레이어1'},
                {'guest_id': 2, 'nickname': '플레이어2'}
            ],
            'used_words': ['끝말잇기', '기차', '차량'],
            'round_number': 3,
            'created_at': datetime.utcnow().isoformat(),
            'game_settings': {'max_rounds': 10}
        }
    
    @pytest.fixture
    def sample_player_stats(self):
        """샘플 플레이어 통계 데이터"""
        return [
            {
                'guest_id': 1,
                'words_submitted': 2,
                'score': 30,
                'total_response_time': 15.0,
                'average_response_time': 7.5,
                'fastest_response': 5.0,
                'slowest_response': 10.0,
                'longest_word': '기차'
            },
            {
                'guest_id': 2,
                'words_submitted': 1,
                'score': 20,
                'total_response_time': 8.0,
                'average_response_time': 8.0,
                'fastest_response': 8.0,
                'slowest_response': 8.0,
                'longest_word': '차량'
            }
        ]
    
    @pytest.fixture
    def sample_word_entries(self):
        """샘플 단어 기록 데이터"""
        return [
            {
                'player_id': 1,
                'word': '끝말잇기',
                'turn_number': 1,
                'round_number': 1,
                'response_time': 5.0,
                'submitted_at': datetime.utcnow().isoformat()
            },
            {
                'player_id': 2,
                'word': '기차',
                'turn_number': 2,
                'round_number': 1,
                'response_time': 8.0,
                'submitted_at': datetime.utcnow().isoformat()
            },
            {
                'player_id': 1,
                'word': '차량',
                'turn_number': 3,
                'round_number': 2,
                'response_time': 10.0,
                'submitted_at': datetime.utcnow().isoformat()
            }
        ]


class TestSaveGameData:
    """게임 데이터 저장 관련 테스트"""
    
    @pytest.mark.asyncio
    async def test_save_game_data_success(self, persistence_service, sample_game_state, sample_player_stats, sample_word_entries):
        """게임 데이터 저장 성공 테스트"""
        room_id = 100
        winner_id = 1
        end_reason = "max_rounds_reached"
        
        # Redis 서비스 Mock 설정
        persistence_service.redis_service.get_game_state = AsyncMock(return_value=sample_game_state)
        persistence_service.redis_service.get_all_player_stats = AsyncMock(return_value=sample_player_stats)
        persistence_service.redis_service.get_word_entries = AsyncMock(return_value=sample_word_entries)
        
        # 게임 로그 저장소 Mock 설정
        mock_game_log = Mock(spec=GameLog)
        mock_game_log.id = 1
        persistence_service.game_log_repository.create = Mock(return_value=mock_game_log)
        
        # 실행
        result = await persistence_service.save_game_data(room_id, winner_id, end_reason)
        
        # 검증
        assert result == mock_game_log
        persistence_service.redis_service.get_game_state.assert_called_once_with(room_id)
        persistence_service.redis_service.get_all_player_stats.assert_called_once_with(room_id)
        persistence_service.game_log_repository.create.assert_called_once()
        persistence_service.db.commit.assert_called_once()
        persistence_service.db.refresh.assert_called_once_with(mock_game_log)
    
    @pytest.mark.asyncio
    async def test_save_game_data_no_game_state(self, persistence_service):
        """게임 상태가 없을 때 저장 실패 테스트"""
        room_id = 999
        
        # Redis에서 게임 상태 없음
        persistence_service.redis_service.get_game_state = AsyncMock(return_value=None)
        
        result = await persistence_service.save_game_data(room_id)
        
        assert result is None
        persistence_service.redis_service.get_game_state.assert_called_once_with(room_id)
        persistence_service.db.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_save_game_data_database_error(self, persistence_service, sample_game_state, sample_player_stats):
        """데이터베이스 오류 시 롤백 테스트"""
        room_id = 100
        
        # Redis 서비스 Mock 설정
        persistence_service.redis_service.get_game_state = AsyncMock(return_value=sample_game_state)
        persistence_service.redis_service.get_all_player_stats = AsyncMock(return_value=sample_player_stats)
        persistence_service.redis_service.get_word_entries = AsyncMock(return_value=[])
        
        # 데이터베이스 오류 시뮬레이션
        persistence_service.game_log_repository.create = Mock(side_effect=Exception("DB 에러"))
        
        result = await persistence_service.save_game_data(room_id)
        
        assert result is None
        persistence_service.db.rollback.assert_called_once()


class TestCreateGameLog:
    """게임 로그 생성 관련 테스트"""
    
    @pytest.mark.asyncio
    async def test_create_game_log_success(self, persistence_service, sample_game_state, sample_player_stats):
        """게임 로그 생성 성공 테스트"""
        room_id = 100
        winner_id = 1
        end_reason = "manual_end"
        
        # Mock 게임 로그 객체
        mock_game_log = Mock(spec=GameLog)
        persistence_service.game_log_repository.create = Mock(return_value=mock_game_log)
        
        result = await persistence_service._create_game_log(
            room_id, sample_game_state, winner_id, end_reason, sample_player_stats
        )
        
        assert result == mock_game_log
        
        # create 메서드가 적절한 데이터로 호출되었는지 확인
        create_call_args = persistence_service.game_log_repository.create.call_args[0][0]
        assert create_call_args['room_id'] == room_id
        assert create_call_args['winner_id'] == winner_id
        assert create_call_args['end_reason'] == end_reason
        assert create_call_args['total_words'] == 3  # used_words 길이
        assert create_call_args['longest_word'] == '끝말잇기'  # 가장 긴 단어
    
    @pytest.mark.asyncio
    async def test_create_game_log_empty_words(self, persistence_service, sample_player_stats):
        """단어가 없는 게임의 로그 생성 테스트"""
        room_id = 100
        game_state = {
            'room_id': 100,
            'used_words': [],
            'created_at': datetime.utcnow().isoformat(),
            'game_settings': {'max_rounds': 10}
        }
        
        mock_game_log = Mock(spec=GameLog)
        persistence_service.game_log_repository.create = Mock(return_value=mock_game_log)
        
        result = await persistence_service._create_game_log(
            room_id, game_state, None, "early_end", sample_player_stats
        )
        
        assert result == mock_game_log
        
        # 빈 단어 리스트 처리 확인
        create_call_args = persistence_service.game_log_repository.create.call_args[0][0]
        assert create_call_args['total_words'] == 0
        assert create_call_args['longest_word'] == ""
    
    @pytest.mark.asyncio
    async def test_create_game_log_exception(self, persistence_service, sample_game_state, sample_player_stats):
        """게임 로그 생성 중 예외 발생 테스트"""
        persistence_service.game_log_repository.create = Mock(side_effect=Exception("생성 실패"))
        
        result = await persistence_service._create_game_log(
            100, sample_game_state, 1, "error", sample_player_stats
        )
        
        assert result is None


class TestSavePlayerGameStats:
    """플레이어 게임 통계 저장 관련 테스트"""
    
    @pytest.mark.asyncio
    async def test_save_player_game_stats_success(self, persistence_service, sample_player_stats):
        """플레이어 통계 저장 성공 테스트"""
        game_log_id = 1
        
        await persistence_service._save_player_game_stats(game_log_id, sample_player_stats)
        
        # PlayerGameStats 객체가 DB에 추가되었는지 확인
        assert persistence_service.db.add.call_count == len(sample_player_stats)
        
        # 첫 번째 플레이어 통계 확인
        first_call_args = persistence_service.db.add.call_args_list[0][0][0]
        assert isinstance(first_call_args, PlayerGameStats)
        assert first_call_args.game_log_id == game_log_id
        assert first_call_args.player_id == sample_player_stats[0]['guest_id']
        assert first_call_args.rank == 1  # 첫 번째 플레이어는 1등
        assert first_call_args.is_winner == 1
    
    @pytest.mark.asyncio
    async def test_save_player_game_stats_ranking(self, persistence_service):
        """플레이어 순위 매기기 테스트"""
        game_log_id = 1
        player_stats = [
            {'guest_id': 1, 'score': 50},  # 1등
            {'guest_id': 2, 'score': 30},  # 2등
            {'guest_id': 3, 'score': 40}   # 2등 (동점이면 원래 순서 유지)
        ]
        
        await persistence_service._save_player_game_stats(game_log_id, player_stats)
        
        # 순위가 올바르게 매겨졌는지 확인
        added_stats = [call[0][0] for call in persistence_service.db.add.call_args_list]
        
        assert added_stats[0].rank == 1  # 첫 번째: 1등
        assert added_stats[1].rank == 2  # 두 번째: 2등  
        assert added_stats[2].rank == 3  # 세 번째: 3등
        
        assert added_stats[0].is_winner == 1  # 1등만 승자
        assert added_stats[1].is_winner == 0
        assert added_stats[2].is_winner == 0
    
    @pytest.mark.asyncio
    async def test_save_player_game_stats_exception(self, persistence_service):
        """플레이어 통계 저장 중 예외 발생 테스트"""
        game_log_id = 1
        player_stats = [{'guest_id': 1}]
        
        persistence_service.db.add.side_effect = Exception("DB 에러")
        
        with pytest.raises(Exception):
            await persistence_service._save_player_game_stats(game_log_id, player_stats)


class TestSaveWordChainEntries:
    """단어 체인 기록 저장 관련 테스트"""
    
    @pytest.mark.asyncio
    async def test_save_word_chain_entries_with_redis_data(self, persistence_service, sample_game_state, sample_player_stats, sample_word_entries):
        """Redis 데이터가 있을 때 단어 체인 기록 저장 테스트"""
        game_log_id = 1
        
        # Redis에서 실제 단어 데이터 반환
        persistence_service.redis_service.get_word_entries = AsyncMock(return_value=sample_word_entries)
        
        await persistence_service._save_word_chain_entries(game_log_id, sample_game_state, sample_player_stats)
        
        # WordChainEntry 객체들이 DB에 추가되었는지 확인
        assert persistence_service.db.add.call_count == len(sample_word_entries)
        
        # 첫 번째 단어 기록 확인
        first_entry = persistence_service.db.add.call_args_list[0][0][0]
        assert isinstance(first_entry, WordChainEntry)
        assert first_entry.game_log_id == game_log_id
        assert first_entry.word == sample_word_entries[0]['word']
        assert first_entry.player_id == sample_word_entries[0]['player_id']
        assert first_entry.is_valid == 1
    
    @pytest.mark.asyncio
    async def test_save_word_chain_entries_fallback_mode(self, persistence_service, sample_game_state, sample_player_stats):
        """Redis 데이터가 없을 때 폴백 모드 테스트"""
        game_log_id = 1
        
        # Redis에서 빈 데이터 반환 (폴백 모드 트리거)
        persistence_service.redis_service.get_word_entries = AsyncMock(return_value=[])
        
        await persistence_service._save_word_chain_entries(game_log_id, sample_game_state, sample_player_stats)
        
        # used_words 기반으로 WordChainEntry가 생성되었는지 확인
        expected_words = sample_game_state['used_words']
        assert persistence_service.db.add.call_count == len(expected_words)
        
        # 플레이어가 라운드 로빈으로 배정되었는지 확인
        added_entries = [call[0][0] for call in persistence_service.db.add.call_args_list]
        
        # 첫 번째 단어는 첫 번째 플레이어
        assert added_entries[0].player_id == sample_game_state['participants'][0]['guest_id']
        assert added_entries[0].word == expected_words[0]
        assert added_entries[0].turn_number == 1
        
        # 두 번째 단어는 두 번째 플레이어
        assert added_entries[1].player_id == sample_game_state['participants'][1]['guest_id']
        assert added_entries[1].word == expected_words[1]
        assert added_entries[1].turn_number == 2
    
    @pytest.mark.asyncio
    async def test_save_word_chain_entries_exception(self, persistence_service, sample_game_state, sample_player_stats):
        """단어 체인 기록 저장 중 예외 발생 테스트"""
        game_log_id = 1
        
        persistence_service.redis_service.get_word_entries = AsyncMock(return_value=[])
        persistence_service.db.add.side_effect = Exception("DB 에러")
        
        with pytest.raises(Exception):
            await persistence_service._save_word_chain_entries(game_log_id, sample_game_state, sample_player_stats)


class TestCalculateRank:
    """순위 계산 관련 테스트"""
    
    def test_calculate_rank_success(self, persistence_service):
        """순위 계산 성공 테스트"""
        all_players = [
            {'guest_id': 1, 'score': 50},
            {'guest_id': 2, 'score': 30},
            {'guest_id': 3, 'score': 40}
        ]
        
        # 각 플레이어의 순위 확인
        rank1 = persistence_service._calculate_rank({'guest_id': 1, 'score': 50}, all_players)
        rank2 = persistence_service._calculate_rank({'guest_id': 2, 'score': 30}, all_players)
        rank3 = persistence_service._calculate_rank({'guest_id': 3, 'score': 40}, all_players)
        
        assert rank1 == 1  # 최고 점수
        assert rank2 == 3  # 최저 점수
        assert rank3 == 2  # 중간 점수
    
    def test_calculate_rank_tie(self, persistence_service):
        """동점자 순위 계산 테스트"""
        all_players = [
            {'guest_id': 1, 'score': 50},
            {'guest_id': 2, 'score': 50},  # 동점
            {'guest_id': 3, 'score': 30}
        ]
        
        rank1 = persistence_service._calculate_rank({'guest_id': 1, 'score': 50}, all_players)
        rank2 = persistence_service._calculate_rank({'guest_id': 2, 'score': 50}, all_players)
        rank3 = persistence_service._calculate_rank({'guest_id': 3, 'score': 30}, all_players)
        
        # 동점자는 원래 순서대로 순위 매겨짐
        assert rank1 == 1
        assert rank2 == 2
        assert rank3 == 3
    
    def test_calculate_rank_not_found(self, persistence_service):
        """플레이어를 찾을 수 없을 때 테스트"""
        all_players = [
            {'guest_id': 1, 'score': 50},
            {'guest_id': 2, 'score': 30}
        ]
        
        # 존재하지 않는 플레이어
        rank = persistence_service._calculate_rank({'guest_id': 999, 'score': 40}, all_players)
        
        assert rank == len(all_players)  # 마지막 순위 반환
    
    def test_calculate_rank_exception(self, persistence_service):
        """순위 계산 중 예외 발생 테스트"""
        # 잘못된 데이터 형식
        with patch('logging.getLogger'):
            rank = persistence_service._calculate_rank(None, [])
            assert rank == 0  # 기본값 반환


class TestGetGameResultData:
    """게임 결과 데이터 조회 관련 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_game_result_data_success(self, persistence_service):
        """게임 결과 데이터 조회 성공 테스트"""
        room_id = 100
        
        # Mock 게임 로그
        mock_game_log = Mock(spec=GameLog)
        mock_game_log.id = 1
        mock_game_log.room_id = room_id
        mock_game_log.winner_id = 1
        mock_game_log.total_rounds = 5
        mock_game_log.total_words = 10
        mock_game_log.average_response_time = 7.5
        mock_game_log.longest_word = "끝말잇기"
        mock_game_log.started_at = datetime.utcnow()
        mock_game_log.ended_at = datetime.utcnow()
        mock_game_log.get_game_duration_formatted = Mock(return_value="5분 30초")
        
        persistence_service.game_log_repository.find_game_log_by_room_id = Mock(return_value=mock_game_log)
        
        # Mock 플레이어 통계
        mock_player_stats = [
            Mock(
                player_id=1, words_submitted=5, total_score=50,
                avg_response_time=6.0, longest_word="기차", rank=1
            ),
            Mock(
                player_id=2, words_submitted=5, total_score=40,
                avg_response_time=8.0, longest_word="자동차", rank=2
            )
        ]
        
        # Mock 단어 기록
        mock_word_entries = [
            Mock(word="끝말잇기", player_id=1, submitted_at=datetime.utcnow(), response_time=5.0),
            Mock(word="기차", player_id=2, submitted_at=datetime.utcnow(), response_time=7.0)
        ]
        
        # Mock 게스트 정보
        mock_guests = [
            Mock(guest_id=1, nickname="플레이어1"),
            Mock(guest_id=2, nickname="플레이어2")
        ]
        
        # DB 쿼리 Mock 설정
        persistence_service.db.query.return_value.filter.return_value.order_by.return_value.all.side_effect = [
            mock_player_stats, mock_word_entries
        ]
        persistence_service.db.query.return_value.filter.return_value.all.return_value = mock_guests
        
        # Redis 통계 Mock (없음)
        persistence_service.redis_service.get_game_stats = AsyncMock(return_value=None)
        
        result = await persistence_service.get_game_result_data(room_id)
        
        # 결과 검증
        assert result is not None
        assert result['room_id'] == room_id
        assert result['winner_id'] == 1
        assert result['winner_name'] == "플레이어1"
        assert len(result['players']) == 2
        assert result['players'][0]['nickname'] == "플레이어1"
        assert result['players'][0]['rank'] == 1
        assert len(result['used_words']) == 2
        assert result['mvp_name'] == "플레이어1"
    
    @pytest.mark.asyncio
    async def test_get_game_result_data_with_redis_stats(self, persistence_service):
        """Redis 통계가 있을 때 게임 결과 데이터 조회 테스트"""
        room_id = 100
        
        # Mock 게임 로그 (평균 응답시간 0)
        mock_game_log = Mock(spec=GameLog)
        mock_game_log.id = 1
        mock_game_log.room_id = room_id
        mock_game_log.average_response_time = 0.0  # DB에는 없음
        mock_game_log.longest_word = ""
        mock_game_log.get_game_duration_formatted = Mock(return_value="3분 20초")
        
        persistence_service.game_log_repository.find_game_log_by_room_id = Mock(return_value=mock_game_log)
        
        # 빈 통계들 Mock
        persistence_service.db.query.return_value.filter.return_value.order_by.return_value.all.side_effect = [
            [], []  # 빈 플레이어 통계, 빈 단어 기록
        ]
        persistence_service.db.query.return_value.filter.return_value.all.return_value = []
        
        # Redis 통계 Mock (있음)
        redis_stats = {
            'fastest_response': 3.0,
            'slowest_response': 12.0,
            'average_response_time': 6.5,
            'longest_word': '끝말잇기'
        }
        persistence_service.redis_service.get_game_stats = AsyncMock(return_value=redis_stats)
        
        result = await persistence_service.get_game_result_data(room_id)
        
        # Redis 통계가 우선 사용되었는지 확인
        assert result['average_response_time'] == 6.5  # Redis 값
        assert result['fastest_response'] == 3.0  # Redis 값
        assert result['slowest_response'] == 12.0  # Redis 값
        assert result['longest_word'] == '끝말잇기'  # Redis 값
    
    @pytest.mark.asyncio
    async def test_get_game_result_data_no_game_log(self, persistence_service):
        """게임 로그가 없을 때 테스트"""
        room_id = 999
        
        persistence_service.game_log_repository.find_game_log_by_room_id = Mock(return_value=None)
        
        result = await persistence_service.get_game_result_data(room_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_game_result_data_exception(self, persistence_service):
        """게임 결과 데이터 조회 중 예외 발생 테스트"""
        room_id = 100
        
        persistence_service.game_log_repository.find_game_log_by_room_id = Mock(
            side_effect=Exception("DB 에러")
        )
        
        result = await persistence_service.get_game_result_data(room_id)
        
        assert result is None


class TestDataIntegrity:
    """데이터 무결성 관련 테스트"""
    
    @pytest.mark.asyncio
    async def test_save_partial_data(self, persistence_service):
        """부분적 데이터 저장 테스트"""
        room_id = 100
        
        # 일부 데이터만 있는 게임 상태
        partial_game_state = {
            'room_id': room_id,
            'used_words': ['테스트'],
            'created_at': datetime.utcnow().isoformat()
            # participants 누락, game_settings 누락
        }
        
        persistence_service.redis_service.get_game_state = AsyncMock(return_value=partial_game_state)
        persistence_service.redis_service.get_all_player_stats = AsyncMock(return_value=[])
        persistence_service.redis_service.get_word_entries = AsyncMock(return_value=[])
        
        mock_game_log = Mock(spec=GameLog)
        mock_game_log.id = 1
        persistence_service.game_log_repository.create = Mock(return_value=mock_game_log)
        
        result = await persistence_service.save_game_data(room_id)
        
        # 부분적 데이터로도 저장이 성공해야 함
        assert result == mock_game_log
        persistence_service.db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_invalid_timestamps(self, persistence_service):
        """잘못된 타임스탬프 처리 테스트"""
        room_id = 100
        
        # 잘못된 타임스탬프가 포함된 게임 상태
        invalid_game_state = {
            'room_id': room_id,
            'used_words': [],
            'created_at': 'invalid-timestamp',  # 잘못된 형식
            'participants': []
        }
        
        persistence_service.redis_service.get_game_state = AsyncMock(return_value=invalid_game_state)
        persistence_service.redis_service.get_all_player_stats = AsyncMock(return_value=[])
        persistence_service.redis_service.get_word_entries = AsyncMock(return_value=[])
        
        # 잘못된 타임스탬프로 인한 예외가 처리되어야 함
        result = await persistence_service.save_game_data(room_id)
        
        # 에러가 발생해도 적절히 처리되어야 함
        assert result is None
        persistence_service.db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, persistence_service, sample_game_state, sample_player_stats):
        """에러 발생 시 트랜잭션 롤백 테스트"""
        room_id = 100
        
        persistence_service.redis_service.get_game_state = AsyncMock(return_value=sample_game_state)
        persistence_service.redis_service.get_all_player_stats = AsyncMock(return_value=sample_player_stats)
        persistence_service.redis_service.get_word_entries = AsyncMock(return_value=[])
        
        # 게임 로그 생성은 성공하지만 플레이어 통계 저장에서 실패
        mock_game_log = Mock(spec=GameLog)
        mock_game_log.id = 1
        persistence_service.game_log_repository.create = Mock(return_value=mock_game_log)
        
        # 플레이어 통계 저장 중 에러 발생
        persistence_service.db.add.side_effect = Exception("플레이어 통계 저장 실패")
        
        result = await persistence_service.save_game_data(room_id)
        
        # 실패 시 롤백되어야 함
        assert result is None
        persistence_service.db.rollback.assert_called_once()
        persistence_service.db.commit.assert_not_called()