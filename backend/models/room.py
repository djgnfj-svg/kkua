from sqlalchemy import Column, Integer, String, Boolean
from db.postgres import Base

# 방 정보 모델
class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)  # 방 제목
    people = Column(Integer, nullable=False)  # 현재 인원
    room_type = Column(String, nullable=False)  # 방 타입 (일반/스피드)
    max_people = Column(Integer, nullable=False, default=4)  # 최대 수용 인원
    playing = Column(Boolean, nullable=False, default=False)  # 게임 진행 상태 