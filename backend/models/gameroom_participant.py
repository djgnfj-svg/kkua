from db.postgres import Base
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
import datetime
import enum

class ParticipantStatus(enum.Enum):
    WAITING = "waiting"
    READY = "ready"
    PLAYING = "playing"
    FINISHED = "finished" #1시간 이상 움직임이 없으면 죽여버린다.
    LEFT = "left"  # 솔직히 있어야하는지 모르겠음... 음....

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