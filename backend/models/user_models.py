from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class User(Base):
    """사용자 모델"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nickname = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    last_login = Column(DateTime(timezone=True))
    total_games = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    total_score = Column(BigInteger, default=0)
    is_active = Column(Boolean, default=True)
    
    # 관계
    user_items = relationship("UserItem", back_populates="user", cascade="all, delete-orphan")
    created_rooms = relationship("GameRoom", back_populates="creator")
    game_participants = relationship("GameParticipant", back_populates="user")
    game_logs = relationship("GameLog", back_populates="user")
    word_submissions = relationship("WordSubmission", back_populates="user")
    won_sessions = relationship("GameSession", back_populates="winner")
    
    def __repr__(self):
        return f"<User(id={self.id}, nickname='{self.nickname}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "nickname": self.nickname,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "total_games": self.total_games,
            "total_wins": self.total_wins,
            "total_score": self.total_score,
            "is_active": self.is_active
        }


class UserItem(Base):
    """사용자 아이템 인벤토리 모델"""
    __tablename__ = "user_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, index=True)
    quantity = Column(Integer, default=1)
    acquired_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    user = relationship("User", back_populates="user_items")
    item = relationship("Item", back_populates="user_items")
    
    def __repr__(self):
        return f"<UserItem(user_id={self.user_id}, item_id={self.item_id}, quantity={self.quantity})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "item_id": self.item_id,
            "quantity": self.quantity,
            "acquired_at": self.acquired_at.isoformat() if self.acquired_at else None,
            "item": self.item.to_dict() if self.item else None
        }