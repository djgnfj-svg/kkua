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
    device_info = Column(String, nullable=True)
    
    # Gameroom만 유지, Room 관계 제거
    gamerooms = relationship("Gameroom", back_populates="creator")
    participations = relationship("GameroomParticipant", back_populates="guest", cascade="all, delete-orphan")