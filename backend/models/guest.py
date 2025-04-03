from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.postgres import Base
import datetime
import uuid

class Guest(Base):
    __tablename__ = "guests"
    guest_id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, index=True)
    nickname = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # 수정된 관계 설정
    rooms = relationship("Room", foreign_keys="Room.created_by", back_populates="creator")
    gamerounds = relationship("Gameround", back_populates="guest")
    gameresults = relationship("Gameresult", back_populates="guest")