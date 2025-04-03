from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
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
    created_by = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # 관계 설정: 게임방 생성자, 해당 게임방의 라운드와 결과
    creator = relationship("Guest", back_populates="gamerooms")
    gamerounds = relationship("Gameround", back_populates="gameroom", cascade="all, delete")
    gameresults = relationship("Gameresult", back_populates="gameroom", cascade="all, delete") 