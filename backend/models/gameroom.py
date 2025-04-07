from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from db.postgres import Base
import datetime

class Gameroom(Base):
    __tablename__ = "gamerooms"
    room_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    max_players = Column(Integer, nullable=False)
    game_mode = Column(String, nullable=False)
    time_limit = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    
    # Room 모델에서 가져온 추가 필드들
    people = Column(Integer, nullable=False, default=1)  # 현재 인원
    room_type = Column(String, nullable=False, default="normal")  # 방 타입
    playing = Column(Boolean, nullable=False, default=False)  # 게임 진행 상태
    
    created_by = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # 관계 설정
    creator = relationship("Guest", back_populates="gamerooms")