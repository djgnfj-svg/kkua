from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from db.postgres import Base
import datetime
import enum

class GameStatus(enum.Enum):
    WAITING = "waiting"
    PLAYING = "playing" 
    FINISHED = "finished"

class Gameroom(Base):
    __tablename__ = "gamerooms"
    room_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    max_players = Column(Integer, nullable=False, default=4)
    game_mode = Column(String, nullable=False, default="normal")
    time_limit = Column(Integer, nullable=False, default=60)
    status = Column(Enum(GameStatus), nullable=False, default=GameStatus.WAITING)
    
    # Room 모델에서 가져온 추가 필드들
    people = Column(Integer, nullable=False, default=1)  # 현재 인원
    room_type = Column(String, nullable=False, default="normal")  # 방 타입
    
    created_by = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # 관계 설정
    creator = relationship("Guest", back_populates="gamerooms")
    participants = relationship("GameroomParticipant", back_populates="gameroom", cascade="all, delete-orphan")
