from db.postgres import Base
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
import datetime
import enum

class ParticipantStatus(enum.Enum):
    WAITING = "waiting"
    READY = "ready"  # 새로 추가: 참가자가 준비됨
    PLAYING = "playing"
    FINISHED = "finished"

class GameroomParticipant(Base):
    __tablename__ = "gameroom_participants"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("gamerooms.room_id"), nullable=False)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)

    status = Column(Enum(ParticipantStatus), nullable=False, default=ParticipantStatus.WAITING)
    
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)
    left_at = Column(DateTime, nullable=True)

    # relationship 설정
    gameroom = relationship("Gameroom", back_populates="participants")
    guest = relationship("Guest", back_populates="participations") 