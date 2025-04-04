from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db.postgres import Base
import datetime

class Gameresult(Base):
    __tablename__ = "gameresults"
    result_id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    score = Column(Integer, nullable=False)
    rank = Column(Integer, nullable=False)
    played_at = Column(DateTime, default=datetime.datetime.utcnow)

    # 관계 설정: 해당 결과가 속한 게임방과 게스트
    room = relationship("Room", back_populates="gameresults")
    guest = relationship("Guest", back_populates="gameresults") 