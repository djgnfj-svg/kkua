from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import datetime
import uuid

from models.gameroom_model import Gameroom, GameStatus
from models.gameroom_participant import GameroomParticipant, ParticipantStatus
from models.guest_model import Guest

class GameroomRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def find_all_active(self) -> List[Gameroom]:
        """종료되지 않은 모든 게임룸을 조회합니다."""
        rooms = self.db.query(Gameroom).filter(Gameroom.status != GameStatus.FINISHED).all()
        
        # 각 방에 대해 created_username 속성 추가
        for room in rooms:
            setattr(room, 'created_username', room.creator.nickname)
        
        return rooms
    
    def find_by_id(self, room_id: int) -> Optional[Gameroom]:
        """ID로 게임룸을 조회합니다."""
        room = self.db.query(Gameroom).filter(Gameroom.room_id == room_id).first()
        if room:
            setattr(room, 'created_username', room.creator.nickname)
        return room
    
    def find_active_by_creator(self, guest_id: int) -> Optional[Gameroom]:
        """특정 게스트가 생성하고 아직 종료되지 않은 게임룸을 조회합니다."""
        return self.db.query(Gameroom).filter(
            Gameroom.created_by == guest_id,
            Gameroom.status != GameStatus.FINISHED
        ).first()
    
    def create(self, room_data: dict, guest_id: int) -> Gameroom:
        """새 게임룸을 생성합니다."""
        db_room = Gameroom(**room_data)
        self.db.add(db_room)
        self.db.commit()
        self.db.refresh(db_room)
        
        # 방 생성자를 참가자로 등록
        creator_participant = GameroomParticipant(
            guest_id=guest_id,
            room_id=db_room.room_id,
            status=ParticipantStatus.WAITING
        )
        self.db.add(creator_participant)
        self.db.commit()
        
        # 생성자 닉네임 설정
        guest = self.db.query(Guest).filter(Guest.guest_id == guest_id).first()
        setattr(db_room, 'created_username', guest.nickname)
        
        return db_room
    
    def update(self, room: Gameroom, update_data: dict) -> Gameroom:
        """게임룸 정보를 업데이트합니다."""
        for key, value in update_data.items():
            if value is not None and hasattr(room, key):
                setattr(room, key, value)
        
        self.db.commit()
        self.db.refresh(room)
        
        setattr(room, 'created_username', room.creator.nickname)
        return room
    
    def delete(self, room: Gameroom) -> None:
        """게임룸을 삭제 처리합니다 (상태를 FINISHED로 변경)."""
        room.status = GameStatus.FINISHED
        self.db.commit()
    
    def find_participant(self, room_id: int, guest_id: int) -> Optional[GameroomParticipant]:
        """특정 게임룸에 참여 중인 참가자를 조회합니다."""
        return self.db.query(GameroomParticipant).filter(
            GameroomParticipant.guest_id == guest_id,
            GameroomParticipant.room_id == room_id,
            GameroomParticipant.left_at.is_(None)  # 아직 나가지 않은 상태
        ).first()
    
    def find_other_participation(self, guest_id: int, excluding_room_id: int) -> Optional[GameroomParticipant]:
        """특정 게스트가 다른 게임룸에 참여 중인지 확인합니다."""
        return self.db.query(GameroomParticipant).filter(
            GameroomParticipant.guest_id == guest_id,
            GameroomParticipant.room_id != excluding_room_id,
            GameroomParticipant.left_at.is_(None)
        ).first()
    
    def add_participant(self, room_id: int, guest_id: int) -> GameroomParticipant:
        """게임룸에 새 참가자를 추가합니다."""
        # 새로운 참가 레코드
        new_participation = GameroomParticipant(
            guest_id=guest_id,
            room_id=room_id,
            status=ParticipantStatus.WAITING
        )
        self.db.add(new_participation)
        
        # 인원수 증가
        room = self.find_by_id(room_id)
        room.participant_count += 1
        
        self.db.commit()
        self.db.refresh(new_participation)
        return new_participation
    
    def remove_participant(self, participation: GameroomParticipant) -> None:
        """참가자를 게임룸에서 제거합니다."""
        participation.left_at = datetime.utcnow()
        participation.status = ParticipantStatus.LEFT
        
        # 인원수 감소
        room = self.find_by_id(participation.room_id)
        if room.participant_count > 0:
            room.participant_count -= 1
        
        self.db.commit()
    
    def update_game_status(self, room: Gameroom, status: GameStatus) -> Gameroom:
        """게임 상태를 업데이트합니다."""
        room.status = status
        
        # 참가자 상태 업데이트
        participant_status = None
        if status == GameStatus.PLAYING:
            participant_status = ParticipantStatus.PLAYING
        elif status == GameStatus.FINISHED:
            participant_status = ParticipantStatus.FINISHED
        
        if participant_status:
            participants = self.db.query(GameroomParticipant).filter(
                GameroomParticipant.room_id == room.room_id,
                GameroomParticipant.left_at.is_(None)
            ).all()
            
            for participant in participants:
                participant.status = participant_status
        
        self.db.commit()
        self.db.refresh(room)
        return room
    
    def find_room_participants(self, room_id: int) -> List[GameroomParticipant]:
        """특정 게임룸의 모든 참가자를 조회합니다."""
        return self.db.query(GameroomParticipant).filter(
            GameroomParticipant.room_id == room_id,
            GameroomParticipant.left_at.is_(None)
        ).all()
    
    def check_active_game(self, guest_uuid: uuid.UUID) -> Tuple[bool, Optional[int]]:
        """게스트가 현재 참여 중인 게임이 있는지 확인합니다."""
        guest = self.db.query(Guest).filter(Guest.uuid == guest_uuid).first()
        if not guest:
            return False, None
        
        return GameroomParticipant.should_redirect_to_game(self.db, guest.guest_id) 