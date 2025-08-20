from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class GameLog(Base):
    """게임 로그 모델"""
    __tablename__ = "game_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    action_type = Column(String(30), nullable=False, index=True)  # word_submit, item_use, game_start 등
    action_data = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    round_number = Column(Integer)
    
    # 관계
    session = relationship("GameSession", back_populates="game_logs")
    user = relationship("User", back_populates="game_logs")
    
    def __repr__(self):
        return f"<GameLog(action_type='{self.action_type}', session_id={self.session_id}, user_id={self.user_id})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "session_id": str(self.session_id),
            "user_id": self.user_id,
            "action_type": self.action_type,
            "action_data": self.action_data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "round_number": self.round_number
        }


class WordSubmission(Base):
    """단어 제출 기록 모델"""
    __tablename__ = "word_submissions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    word = Column(String(100), nullable=False, index=True)
    is_valid = Column(Boolean, nullable=False)
    validation_reason = Column(String(100))  # 검증 실패 이유
    response_time_ms = Column(Integer)
    score_earned = Column(Integer, default=0)
    round_number = Column(Integer)
    turn_order = Column(Integer)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 관계
    session = relationship("GameSession", back_populates="word_submissions")
    user = relationship("User", back_populates="word_submissions")
    
    def __repr__(self):
        return f"<WordSubmission(word='{self.word}', is_valid={self.is_valid}, user_id={self.user_id})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "session_id": str(self.session_id),
            "user_id": self.user_id,
            "word": self.word,
            "is_valid": self.is_valid,
            "validation_reason": self.validation_reason,
            "response_time_ms": self.response_time_ms,
            "score_earned": self.score_earned,
            "round_number": self.round_number,
            "turn_order": self.turn_order,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "user": self.user.to_dict() if self.user else None
        }
    
    @classmethod
    def get_validation_reasons(cls):
        """검증 실패 이유 목록"""
        return {
            "INVALID_WORD": "존재하지 않는 단어입니다",
            "WRONG_FIRST_CHAR": "끝말잇기 규칙에 맞지 않습니다", 
            "DUPLICATE_WORD": "이미 사용된 단어입니다",
            "TOO_SHORT": "단어가 너무 짧습니다",
            "TOO_LONG": "단어가 너무 깁니다",
            "TIMEOUT": "시간이 초과되었습니다",
            "INAPPROPRIATE": "부적절한 단어입니다"
        }