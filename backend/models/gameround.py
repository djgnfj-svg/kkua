from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db.postgres import Base
import datetime

class Gameround(Base):
    __tablename__ = "gamerounds"
    round_id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    word = Column(String, nullable=False)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

    # 관계 설정: 해당 라운드가 속한 게임방과 제출한 게스트
    room = relationship("Room", back_populates="gamerounds")
    guest = relationship("Guest", back_populates="gamerounds") 