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
    
    @classmethod
    def get_active_game_for_user(cls, db, guest_id):
        """유저가 현재 참여 중인 게임을 찾아 반환합니다."""
        participant = db.query(cls).filter(
            cls.guest_id == guest_id,
            cls.status.in_([ParticipantStatus.PLAYING, ParticipantStatus.WAITING]),
            cls.left_at.is_(None)
        ).first()
        return participant
    @classmethod
    def should_redirect_to_game(cls, db, guest_id):
        """
        유저가 게임 중인지 확인하고 게임방으로 리다이렉트해야 하는지 여부를 반환합니다.
        게임 중이라면 해당 방 ID를 함께 반환합니다.
        """
        active_game = cls.get_active_game_for_user(db, guest_id)
        if active_game:
            return True, active_game.room_id
        return False, None
    
    def mark_as_left(self):
        """유저가 방을 나갔을 때 상태를 업데이트합니다."""
        self.status = ParticipantStatus.LEFT
        self.left_at = datetime.datetime.utcnow() 