from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from db.postgres import Base
import datetime
import enum
import uuid
from sqlalchemy import text

class GameStatus(enum.Enum):
    WAITING = "waiting"
    PLAYING = "playing" 
    FINISHED = "finished"

class ParticipantStatus(enum.Enum):
    WAITING = "waiting"   # 대기 중
    READY = "ready"       # 준비 완료
    PLAYING = "playing"   # 게임 중
    LEFT = "left"         # 나감

class Gameroom(Base):
    __tablename__ = "gamerooms"
    room_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    max_players = Column(Integer, nullable=False, default=4)
    game_mode = Column(String, nullable=False, default="normal")
    time_limit = Column(Integer, nullable=False, default=60)
    status = Column(Enum(GameStatus), nullable=False, default=GameStatus.WAITING)
    
    # Room 모델에서 가져온 추가 필드들
    participant_count = Column(Integer, nullable=False, default=1)  # 현재 참여자 수
    room_type = Column(String, nullable=False, default="normal")  # 방 타입
    
    created_by = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # 관계 설정
    creator = relationship("Guest", back_populates="gamerooms")
    participants = relationship("GameroomParticipant", back_populates="gameroom", cascade="all, delete-orphan")

class GameroomParticipant(Base):
    __tablename__ = "gameroom_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("gamerooms.room_id", ondelete="CASCADE"), nullable=False)
    guest_id = Column(Integer, ForeignKey("guests.guest_id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)
    left_at = Column(DateTime, nullable=True)  # 나간 시간 (NULL이면 아직 방에 있음)
    status = Column(Enum(ParticipantStatus), nullable=False, default=ParticipantStatus.WAITING)
    
    # 관계 설정
    gameroom = relationship("Gameroom", back_populates="participants")
    guest = relationship("Guest")
    
    @staticmethod
    def should_redirect_to_game(db, guest_id):
        """게스트가 활성화된 게임방에 참여 중인지 확인하고 리다이렉트해야 하는지 결정합니다."""
        # UUID를 정수로 변환 (guest_id가 UUID 객체인 경우 정수로 변환)
        if isinstance(guest_id, uuid.UUID):
            # guest_repository에서 실제 guest_id 정수 값 가져오기
            guest = db.execute(
                text("SELECT guest_id FROM guests WHERE uuid = :uuid"),
                {"uuid": guest_id}
            ).fetchone()
            
            if guest:
                guest_id = guest[0]  # 실제 정수 guest_id
                print(f"UUID를 정수 guest_id로 변환: {guest_id}")
            else:
                print(f"UUID에 해당하는 게스트를 찾을 수 없음: {guest_id}")
                return False, None
        
        # 정수 guest_id로 참가 중인 방 찾기
        participant = db.query(GameroomParticipant).filter(
            GameroomParticipant.guest_id == guest_id,
            GameroomParticipant.left_at.is_(None)
        ).first()
        
        if participant:
            room = db.query(Gameroom).filter(
                Gameroom.room_id == participant.room_id
            ).first()
            
            if room and room.status != GameStatus.FINISHED:
                return True, room.room_id
                
        return False, None
