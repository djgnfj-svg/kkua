from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from db.postgres import Base
import enum
from datetime import datetime
import uuid
from models.guest_model import Guest


class GameStatus(str, enum.Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"


class ParticipantStatus(str, enum.Enum):
    WAITING = "waiting"  # 대기 중
    READY = "ready"  # 준비 완료
    PLAYING = "playing"  # 게임 중
    LEFT = "left"  # 나감


class Gameroom(Base):
    __tablename__ = "gamerooms"

    room_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    max_players = Column(Integer, nullable=False, default=8)
    game_mode = Column(String, nullable=False, default="standard")
    time_limit = Column(Integer, nullable=False, default=300)
    status = Column(
        String, nullable=False, default=GameStatus.WAITING.value
    )  # Enum.value로 저장
    created_by = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    participant_count = Column(Integer, nullable=False, default=0)
    room_type = Column(String, nullable=False, default="normal")

    creator = relationship("Guest")
    participants = relationship(
        "GameroomParticipant", back_populates="gameroom", cascade="all, delete-orphan"
    )


class GameroomParticipant(Base):
    __tablename__ = "gameroom_participants"

    participant_id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("gamerooms.room_id"), nullable=False)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    joined_at = Column(DateTime, nullable=False, default=datetime.now)
    left_at = Column(DateTime, nullable=True)
    status = Column(
        String, nullable=False, default=ParticipantStatus.WAITING.value
    )  # Enum.value로 저장
    is_creator = Column(Boolean, nullable=False, default=False)  # 방장 여부 추가

    gameroom = relationship("Gameroom", back_populates="participants")
    guest = relationship("Guest")

    @staticmethod
    def should_redirect_to_game(db, guest_id):
        """게스트가 활성화된 게임방에 참여 중인지 확인하고 리다이렉트해야 하는지 결정합니다."""
        if isinstance(guest_id, uuid.UUID):
            guest = db.query(Guest).filter(Guest.uuid == guest_id).first()
            if not guest:
                return False, None
            guest_id = guest.guest_id

        participant = (
            db.query(GameroomParticipant)
            .filter(
                GameroomParticipant.guest_id == guest_id,
                GameroomParticipant.left_at.is_(None),
                GameroomParticipant.status != ParticipantStatus.LEFT,
            )
            .first()
        )

        if participant:
            room = (
                db.query(Gameroom)
                .filter(Gameroom.room_id == participant.room_id)
                .first()
            )

            if room and room.status != GameStatus.FINISHED:
                return True, room.room_id

        return False, None
