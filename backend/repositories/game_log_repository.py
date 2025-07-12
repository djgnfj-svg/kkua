from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import Optional, List
from datetime import datetime

from models.game_log_model import GameLog
from models.word_chain_entry_model import WordChainEntry
from models.player_game_stats_model import PlayerGameStats

class GameLogRepository:
    """게임 로그 관련 데이터베이스 작업을 처리하는 Repository"""
    
    def __init__(self, db: Session):
        self.db = db

    def create_game_log(self, room_id: int, max_rounds: int) -> GameLog:
        """새 게임 로그를 생성합니다"""
        game_log = GameLog(
            room_id=room_id,
            max_rounds=max_rounds,
            started_at=datetime.utcnow()
        )
        self.db.add(game_log)
        self.db.commit()
        self.db.refresh(game_log)
        return game_log

    def find_game_log_by_room_id(self, room_id: int) -> Optional[GameLog]:
        """방 ID로 최신 게임 로그를 조회합니다"""
        return self.db.query(GameLog).filter(
            GameLog.room_id == room_id
        ).order_by(desc(GameLog.created_at)).first()

    def end_game_log(self, game_log_id: int, winner_id: Optional[int] = None, 
                     end_reason: str = "completed") -> Optional[GameLog]:
        """게임 로그를 종료 상태로 업데이트합니다"""
        game_log = self.db.query(GameLog).filter(GameLog.id == game_log_id).first()
        if game_log:
            game_log.ended_at = datetime.utcnow()
            game_log.winner_id = winner_id
            game_log.end_reason = end_reason
            game_log.calculate_game_duration()
            
            # 통계 계산
            self._calculate_game_statistics(game_log)
            
            self.db.commit()
            self.db.refresh(game_log)
        return game_log

    def add_word_entry(self, game_log_id: int, player_id: int, word: str, 
                      turn_number: int, round_number: int, response_time: float) -> WordChainEntry:
        """단어 엔트리를 추가합니다"""
        entry = WordChainEntry(
            game_log_id=game_log_id,
            player_id=player_id,
            word=word,
            turn_number=turn_number,
            round_number=round_number,
            response_time=response_time,
            submitted_at=datetime.utcnow()
        )
        
        # 점수 계산
        entry.calculate_word_score()
        
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_word_entries_by_game_log(self, game_log_id: int) -> List[WordChainEntry]:
        """게임 로그 ID로 단어 엔트리 목록을 조회합니다"""
        return self.db.query(WordChainEntry).filter(
            WordChainEntry.game_log_id == game_log_id
        ).order_by(asc(WordChainEntry.turn_number)).all()

    def create_player_stats(self, game_log_id: int, player_id: int) -> PlayerGameStats:
        """플레이어 게임 통계를 생성합니다"""
        stats = PlayerGameStats(
            game_log_id=game_log_id,
            player_id=player_id
        )
        self.db.add(stats)
        self.db.commit()
        self.db.refresh(stats)
        return stats

    def get_player_stats_by_game_log(self, game_log_id: int) -> List[PlayerGameStats]:
        """게임 로그 ID로 플레이어 통계 목록을 조회합니다"""
        return self.db.query(PlayerGameStats).filter(
            PlayerGameStats.game_log_id == game_log_id
        ).order_by(asc(PlayerGameStats.rank)).all()

    def update_player_stats(self, game_log_id: int, player_id: int, 
                           word: str, response_time: float, score: int) -> Optional[PlayerGameStats]:
        """플레이어 통계를 업데이트합니다"""
        stats = self.db.query(PlayerGameStats).filter(
            PlayerGameStats.game_log_id == game_log_id,
            PlayerGameStats.player_id == player_id
        ).first()
        
        if stats:
            stats.update_word_stats(word, response_time, score)
            self.db.commit()
            self.db.refresh(stats)
        
        return stats

    def calculate_final_rankings(self, game_log_id: int):
        """최종 순위를 계산하고 저장합니다"""
        stats_list = self.db.query(PlayerGameStats).filter(
            PlayerGameStats.game_log_id == game_log_id
        ).order_by(desc(PlayerGameStats.total_score)).all()
        
        for rank, stats in enumerate(stats_list, 1):
            stats.rank = rank
            stats.is_winner = 1 if rank == 1 else 0
            
        self.db.commit()
        
        # 승자 ID 반환 (1위)
        if stats_list:
            return stats_list[0].player_id
        return None

    def _calculate_game_statistics(self, game_log: GameLog):
        """게임 전체 통계를 계산합니다"""
        # 단어 엔트리들 조회
        entries = self.get_word_entries_by_game_log(game_log.id)
        
        if entries:
            game_log.total_words = len(entries)
            
            # 응답 시간 통계
            response_times = [e.response_time for e in entries if e.response_time]
            if response_times:
                game_log.average_response_time = round(sum(response_times) / len(response_times), 2)
                game_log.fastest_response_time = min(response_times)
                game_log.slowest_response_time = max(response_times)
            
            # 가장 긴 단어
            longest_entry = max(entries, key=lambda e: len(e.word))
            game_log.longest_word = longest_entry.word
            
            # 라운드 수 업데이트
            if entries:
                game_log.total_rounds = max(e.round_number for e in entries)

    def get_game_log_with_details(self, game_log_id: int) -> Optional[GameLog]:
        """상세 정보가 포함된 게임 로그를 조회합니다"""
        return self.db.query(GameLog).filter(GameLog.id == game_log_id).first()

    def find_recent_games_by_player(self, player_id: int, limit: int = 10) -> List[GameLog]:
        """플레이어의 최근 게임 기록을 조회합니다"""
        return self.db.query(GameLog).join(PlayerGameStats).filter(
            PlayerGameStats.player_id == player_id
        ).order_by(desc(GameLog.created_at)).limit(limit).all()