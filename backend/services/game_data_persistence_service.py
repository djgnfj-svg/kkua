"""
게임 데이터 영속성 서비스 - Redis에서 PostgreSQL로 게임 데이터 저장
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from models.game_log_model import GameLog
from models.player_game_stats_model import PlayerGameStats
from models.word_chain_entry_model import WordChainEntry
from models.guest_model import Guest
from repositories.game_log_repository import GameLogRepository
from services.redis_game_service import RedisGameService

logger = logging.getLogger(__name__)


class GameDataPersistenceService:
    """Redis 게임 데이터를 PostgreSQL에 영구 저장하는 서비스"""
    
    def __init__(self, db: Session, redis_service: RedisGameService):
        self.db = db
        self.redis_service = redis_service
        self.game_log_repository = GameLogRepository(db)
    
    async def save_game_data(self, room_id: int, winner_id: Optional[int] = None, 
                           end_reason: str = "manual_end") -> Optional[GameLog]:
        """
        Redis의 게임 데이터를 PostgreSQL에 저장합니다.
        
        Args:
            room_id: 게임룸 ID
            winner_id: 승자 ID (없으면 무승부)
            end_reason: 게임 종료 사유
            
        Returns:
            GameLog: 저장된 게임 로그 객체
        """
        try:
            # Redis에서 게임 상태 조회
            game_state = await self.redis_service.get_game_state(room_id)
            if not game_state:
                logger.warning(f"게임 상태를 찾을 수 없음: room_id={room_id}")
                return None
            
            # 모든 플레이어 통계 조회
            all_player_stats = await self.redis_service.get_all_player_stats(room_id)
            
            # 게임 로그 생성
            game_log = await self._create_game_log(
                room_id, game_state, winner_id, end_reason, all_player_stats
            )
            
            if not game_log:
                return None
            
            # 플레이어별 게임 통계 저장
            await self._save_player_game_stats(game_log.id, all_player_stats)
            
            # 단어 체인 기록 저장
            await self._save_word_chain_entries(game_log.id, game_state, all_player_stats)
            
            self.db.commit()
            self.db.refresh(game_log)
            
            logger.info(f"게임 데이터 저장 완료: room_id={room_id}, game_log_id={game_log.id}")
            return game_log
            
        except Exception as e:
            logger.error(f"게임 데이터 저장 실패: {e}")
            self.db.rollback()
            return None
    
    async def _create_game_log(self, room_id: int, game_state: Dict, 
                             winner_id: Optional[int], end_reason: str,
                             player_stats: List[Dict]) -> Optional[GameLog]:
        """게임 로그를 생성합니다."""
        try:
            # 게임 시간 계산
            started_at = datetime.fromisoformat(game_state.get('created_at', datetime.utcnow().isoformat()))
            ended_at = datetime.utcnow()
            game_duration = int((ended_at - started_at).total_seconds())
            
            # 통계 계산
            used_words = game_state.get('used_words', [])
            total_words = len(used_words)
            longest_word = max(used_words, key=len) if used_words else ""
            
            # 응답 시간 통계 계산
            response_times = []
            for stats in player_stats:
                # Redis 플레이어 통계에서 응답 시간 정보 추출 (향후 구현)
                pass
            
            average_response_time = sum(response_times) / len(response_times) if response_times else 0
            fastest_response = min(response_times) if response_times else 0
            slowest_response = max(response_times) if response_times else 0
            
            # GameLog 객체 생성
            game_log_data = {
                'room_id': room_id,
                'winner_id': winner_id,
                'started_at': started_at,
                'ended_at': ended_at,
                'total_rounds': game_state.get('round_number', 0),
                'max_rounds': game_state.get('game_settings', {}).get('max_rounds', 10),
                'game_duration_seconds': game_duration,
                'end_reason': end_reason,
                'total_words': total_words,
                'average_response_time': average_response_time,
                'longest_word': longest_word,
                'fastest_response_time': fastest_response,
                'slowest_response_time': slowest_response
            }
            
            return self.game_log_repository.create(game_log_data)
            
        except Exception as e:
            logger.error(f"게임 로그 생성 실패: {e}")
            return None
    
    async def _save_player_game_stats(self, game_log_id: int, player_stats: List[Dict]):
        """플레이어별 게임 통계를 저장합니다."""
        try:
            for rank, stats in enumerate(player_stats, 1):
                # Redis에서 가져온 상세 통계 사용
                player_stat_data = {
                    'game_log_id': game_log_id,
                    'player_id': stats.get('guest_id'),
                    'words_submitted': stats.get('words_submitted', 0),
                    'valid_words': stats.get('words_submitted', 0),  # 모든 단어가 유효하다고 가정
                    'invalid_words': 0,
                    'total_score': stats.get('score', 0),
                    'word_score': stats.get('score', 0),
                    'bonus_score': 0,
                    'total_response_time': stats.get('total_response_time', 0.0),
                    'avg_response_time': stats.get('average_response_time', 0.0),
                    'fastest_response_time': stats.get('fastest_response', 0.0),
                    'slowest_response_time': stats.get('slowest_response', 0.0),
                    'longest_word': stats.get('longest_word', ''),
                    'longest_word_length': len(stats.get('longest_word', '')),
                    'shortest_word': '',  # 향후 구현
                    'shortest_word_length': 0,
                    'rank': rank,
                    'is_winner': 1 if rank == 1 else 0,
                    'time_violations': 0,  # 향후 구현
                    'consecutive_words': 0  # 향후 구현
                }
                
                # PlayerGameStats 저장
                player_game_stats = PlayerGameStats(**player_stat_data)
                self.db.add(player_game_stats)
                
        except Exception as e:
            logger.error(f"플레이어 통계 저장 실패: {e}")
            raise
    
    async def _save_word_chain_entries(self, game_log_id: int, game_state: Dict, 
                                     player_stats: List[Dict]):
        """단어 체인 기록을 저장합니다."""
        try:
            # Redis에서 실제 단어 데이터 가져오기
            room_id = game_state.get('room_id')
            word_entries = await self.redis_service.get_word_entries(room_id) if room_id else []
            
            if word_entries:
                # Redis에서 가져온 실제 데이터 사용
                for word_entry in word_entries:
                    word_entry_data = {
                        'game_log_id': game_log_id,
                        'player_id': word_entry.get('player_id'),
                        'word': word_entry.get('word', ''),
                        'turn_number': word_entry.get('turn_number', 1),
                        'round_number': word_entry.get('round_number', 1),
                        'response_time': word_entry.get('response_time', 0.0),
                        'submitted_at': datetime.fromisoformat(word_entry['submitted_at']) if word_entry.get('submitted_at') else datetime.utcnow(),
                        'is_valid': 1,
                        'validation_message': None,
                        'word_score': len(word_entry.get('word', '')) * 10,  # 글자당 10점
                        'bonus_score': 0
                    }
                    
                    word_chain_entry = WordChainEntry(**word_entry_data)
                    self.db.add(word_chain_entry)
            else:
                # 폴백: 기존 방식 사용
                used_words = game_state.get('used_words', [])
                participants = game_state.get('participants', [])
                
                # 플레이어 ID 매핑 생성
                player_map = {p['guest_id']: p['nickname'] for p in participants}
                
                # 단어별로 WordChainEntry 생성
                for index, word in enumerate(used_words):
                    # 순서대로 플레이어 결정 (라운드 로빈)
                    player_index = index % len(participants) if participants else 0
                    current_player = participants[player_index] if participants else None
                    
                    if current_player:
                        word_entry_data = {
                            'game_log_id': game_log_id,
                            'player_id': current_player['guest_id'],
                            'word': word,
                            'turn_number': index + 1,
                            'response_time': 0.0,  # 기본값
                            'submitted_at': datetime.utcnow(),
                            'is_valid': 1,
                            'validation_message': None,
                            'word_score': len(word) * 10,  # 글자당 10점
                            'bonus_score': 0
                        }
                        
                        word_entry = WordChainEntry(**word_entry_data)
                        self.db.add(word_entry)
                    
        except Exception as e:
            logger.error(f"단어 체인 기록 저장 실패: {e}")
            raise
    
    def _calculate_rank(self, current_player: Dict, all_players: List[Dict]) -> int:
        """플레이어의 순위를 계산합니다."""
        try:
            # 점수순으로 정렬하여 순위 계산
            sorted_players = sorted(all_players, key=lambda x: x.get('score', 0), reverse=True)
            
            for rank, player in enumerate(sorted_players, 1):
                if player.get('guest_id') == current_player.get('guest_id'):
                    return rank
            
            return len(all_players)  # 기본값
            
        except Exception as e:
            logger.error(f"순위 계산 실패: {e}")
            return 0
    
    async def get_game_result_data(self, room_id: int) -> Optional[Dict[str, Any]]:
        """
        특정 게임룸의 결과 데이터를 프론트엔드 형식에 맞게 조회합니다.
        
        Args:
            room_id: 게임룸 ID
            
        Returns:
            Dict: 게임 결과 데이터 (프론트엔드 형식)
        """
        try:
            # 최신 게임 로그 조회
            game_log = self.game_log_repository.find_game_log_by_room_id(room_id)
            if not game_log:
                return None
            
            # 플레이어 통계 조회 (직접 import)
            from models.player_game_stats_model import PlayerGameStats
            from models.word_chain_entry_model import WordChainEntry
            
            player_stats = self.db.query(PlayerGameStats).filter(
                PlayerGameStats.game_log_id == game_log.id
            ).order_by(PlayerGameStats.rank).all()
            
            # 단어 체인 기록 조회
            word_entries = self.db.query(WordChainEntry).filter(
                WordChainEntry.game_log_id == game_log.id
            ).order_by(WordChainEntry.turn_number).all()
            
            # 게스트 정보 조회
            guest_ids = [stat.player_id for stat in player_stats]
            guests = self.db.query(Guest).filter(Guest.guest_id.in_(guest_ids)).all()
            guest_map = {g.guest_id: g for g in guests}
            
            # 플레이어 데이터 구성
            players_data = []
            for stat in player_stats:
                guest = guest_map.get(stat.player_id)
                players_data.append({
                    'guest_id': stat.player_id,
                    'nickname': guest.nickname if guest else '알 수 없음',
                    'words_submitted': stat.words_submitted,
                    'total_score': stat.total_score,
                    'avg_response_time': stat.avg_response_time or 0.0,
                    'longest_word': stat.longest_word or '없음',
                    'rank': stat.rank
                })
            
            # 단어 체인 데이터 구성
            used_words_data = []
            for entry in word_entries:
                guest = guest_map.get(entry.player_id)
                used_words_data.append({
                    'word': entry.word,
                    'player_id': entry.player_id,
                    'player_name': guest.nickname if guest else '알 수 없음',
                    'timestamp': entry.submitted_at,
                    'response_time': entry.response_time or 0.0
                })
            
            # Redis에서 게임 통계 가져오기 (우선)
            redis_stats = await self.redis_service.get_game_stats(room_id)
            
            if redis_stats:
                fastest_response = redis_stats.get('fastest_response', 0.0) or 0.0
                slowest_response = redis_stats.get('slowest_response', 0.0) or 0.0
                average_response_time_redis = redis_stats.get('average_response_time', 0.0) or 0.0
                
                # Redis 통계가 있으면 사용, 없으면 DB에서 계산
                if game_log.average_response_time == 0.0 and average_response_time_redis > 0.0:
                    average_response_time_override = average_response_time_redis
                else:
                    average_response_time_override = game_log.average_response_time or 0.0
            else:
                # 폴백: DB에서 응답 시간 통계 계산
                response_times = [entry.response_time for entry in word_entries if entry.response_time and entry.response_time > 0]
                fastest_response = min(response_times) if response_times else 0.0
                slowest_response = max(response_times) if response_times else 0.0
                average_response_time_override = game_log.average_response_time or 0.0
            
            # MVP 결정 (1위 플레이어)
            mvp_name = players_data[0]['nickname'] if players_data else '없음'
            
            # 승자 정보
            winner_nickname = None
            if game_log.winner_id and game_log.winner_id in guest_map:
                winner_nickname = guest_map[game_log.winner_id].nickname
            elif players_data:
                winner_nickname = players_data[0]['nickname']  # 1위를 승자로
            
            # 프론트엔드 형식으로 데이터 구성
            return {
                'room_id': game_log.room_id,
                'winner_id': game_log.winner_id,
                'winner_name': winner_nickname,
                'players': players_data,
                'used_words': used_words_data,
                'total_rounds': game_log.total_rounds,
                'game_duration': game_log.get_game_duration_formatted(),
                'total_words': game_log.total_words,
                'average_response_time': average_response_time_override,
                'longest_word': redis_stats.get('longest_word') if redis_stats and redis_stats.get('longest_word') else game_log.longest_word or '없음',
                'fastest_response': fastest_response,
                'slowest_response': slowest_response,
                'mvp_id': players_data[0]['guest_id'] if players_data else None,
                'mvp_name': mvp_name,
                'started_at': game_log.started_at,
                'ended_at': game_log.ended_at
            }
            
        except Exception as e:
            logger.error(f"게임 결과 데이터 조회 실패: {e}")
            return None