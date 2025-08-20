import uuid
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class GameRoom(Base):
    """게임 룸 모델"""
    __tablename__ = "game_rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    max_players = Column(Integer, default=4)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default="waiting", index=True)  # waiting, playing, finished
    settings = Column(JSON, default=dict)
    
    # 관계
    creator = relationship("User", back_populates="created_rooms")
    game_sessions = relationship("GameSession", back_populates="room")
    
    def __repr__(self):
        return f"<GameRoom(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "max_players": self.max_players,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "status": self.status,
            "settings": self.settings
        }


class GameSession(Base):
    """게임 세션 모델"""
    __tablename__ = "game_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("game_rooms.id"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    ended_at = Column(DateTime(timezone=True))
    winner_id = Column(Integer, ForeignKey("users.id"))
    total_rounds = Column(Integer, default=0)
    total_words = Column(Integer, default=0)
    duration_ms = Column(BigInteger)
    game_data = Column(JSON)  # 게임 상세 데이터
    final_scores = Column(JSON)  # 최종 점수 정보
    
    # 관계
    room = relationship("GameRoom", back_populates="game_sessions")
    winner = relationship("User", back_populates="won_sessions")
    participants = relationship("GameParticipant", back_populates="session")
    game_logs = relationship("GameLog", back_populates="session")
    word_submissions = relationship("WordSubmission", back_populates="session")
    
    def __repr__(self):
        return f"<GameSession(id={self.id}, room_id={self.room_id}, status={'finished' if self.ended_at else 'playing'})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "room_id": str(self.room_id),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "winner_id": self.winner_id,
            "total_rounds": self.total_rounds,
            "total_words": self.total_words,
            "duration_ms": self.duration_ms,
            "game_data": self.game_data,
            "final_scores": self.final_scores
        }


class GameParticipant(Base):
    """게임 참가자 모델"""
    __tablename__ = "game_participants"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    final_score = Column(Integer, default=0)
    final_rank = Column(Integer)
    words_submitted = Column(Integer, default=0)
    items_used = Column(Integer, default=0)
    avg_response_time_ms = Column(Integer)
    max_combo = Column(Integer, default=0)
    accuracy_rate = Column(Integer, default=0)  # 정확도 (0-10000, 소수점 4자리까지 표현)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    session = relationship("GameSession", back_populates="participants")
    user = relationship("User", back_populates="game_participants")
    
    def __repr__(self):
        return f"<GameParticipant(session_id={self.session_id}, user_id={self.user_id}, score={self.final_score})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "session_id": str(self.session_id),
            "user_id": self.user_id,
            "final_score": self.final_score,
            "final_rank": self.final_rank,
            "words_submitted": self.words_submitted,
            "items_used": self.items_used,
            "avg_response_time_ms": self.avg_response_time_ms,
            "max_combo": self.max_combo,
            "accuracy_rate": self.accuracy_rate / 10000.0 if self.accuracy_rate is not None else None,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "user": self.user.to_dict() if self.user else None
        }