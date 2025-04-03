from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from db.postgres import Base
import datetime

# 통합된 방 정보 모델
class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)  # 방 제목
    people = Column(Integer, nullable=False)  # 현재 인원
    room_type = Column(String, nullable=False)  # 방 타입 (일반/스피드)
    max_people = Column(Integer, nullable=False, default=4)  # 최대 수용 인원
    playing = Column(Boolean, nullable=False, default=False)  # 게임 진행 상태
    
    # Gameroom에서 추가될 필드
    game_mode = Column(String, nullable=True)  # 게임 모드
    time_limit = Column(Integer, nullable=True)  # 제한 시간 (초)
    status = Column(String, nullable=True, default="waiting")  # 방 상태 (waiting, playing, finished)
    
    # Guest 모델과 연결
    created_by = Column(Integer, ForeignKey("guests.guest_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # 관계 설정
    creator = relationship("Guest")
    gamerounds = relationship("Gameround", back_populates="room")
    gameresults = relationship("Gameresult", back_populates="room") 