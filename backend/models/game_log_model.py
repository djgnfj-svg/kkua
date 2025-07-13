from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from db.postgres import Base

class GameLog(Base):
    """게임 로그 모델 - 게임 전체의 진행 기록을 저장"""
    __tablename__ = "game_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("gamerooms.room_id"), nullable=False, index=True)
    winner_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=True)
    
    # 게임 진행 정보
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    total_rounds = Column(Integer, nullable=False, default=0)
    max_rounds = Column(Integer, nullable=False, default=10)
    game_duration_seconds = Column(Integer, nullable=True)  # 게임 지속 시간 (초)
    
    # 게임 종료 사유
    end_reason = Column(String(50), nullable=True)  # 'max_rounds_reached', 'time_out', 'manual_end' 등
    
    # 통계 정보
    total_words = Column(Integer, nullable=False, default=0)
    average_response_time = Column(Float, nullable=True)
    longest_word = Column(String(100), nullable=True)
    fastest_response_time = Column(Float, nullable=True)
    slowest_response_time = Column(Float, nullable=True)
    
    # 생성/수정 시간
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정은 순환 import 문제로 인해 주석 처리
    # gameroom = relationship("Gameroom", back_populates="game_logs")
    # winner = relationship("Guest", foreign_keys=[winner_id])
    # word_chain_entries = relationship("WordChainEntry", back_populates="game_log", cascade="all, delete-orphan")
    # player_game_stats = relationship("PlayerGameStats", back_populates="game_log", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<GameLog(id={self.id}, room_id={self.room_id}, winner_id={self.winner_id}, total_words={self.total_words})>"

    def calculate_game_duration(self):
        """게임 지속 시간을 계산합니다"""
        if self.started_at and self.ended_at:
            duration = self.ended_at - self.started_at
            self.game_duration_seconds = int(duration.total_seconds())
            return self.game_duration_seconds
        return None

    def get_game_duration_formatted(self):
        """게임 지속 시간을 포맷된 문자열로 반환합니다"""
        if self.game_duration_seconds:
            minutes = self.game_duration_seconds // 60
            seconds = self.game_duration_seconds % 60
            return f"{minutes}분 {seconds}초"
        return "0분 0초"