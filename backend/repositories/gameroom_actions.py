from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from repositories.gameroom_repository import GameroomRepository
from repositories.guest_repository import GuestRepository
from models.gameroom_model import Gameroom, GameStatus, GameroomParticipant, ParticipantStatus

class GameroomActions:
    def __init__(self, db: Session):
        self.db = db
        self.gameroom_repo = GameroomRepository(db)
        self.guest_repo = GuestRepository(db)
    
    def create_gameroom(self, data: Dict[str, Any], guest_id: int) -> Tuple[Gameroom, GameroomParticipant]:
        """
        게임룸을 생성하고 방장을 추가합니다.
        """
        try:
            # 트랜잭션 시작
            # 1. 게임룸 생성
            room_data = data.copy()
            room_data["created_by"] = guest_id
            new_room = self.gameroom_repo.create(room_data)
            
            # 2. 방장을 참가자로 추가
            participant = self.gameroom_repo.add_participant(
                room_id=new_room.room_id,
                guest_id=guest_id,
                is_creator=True
            )
            
            # 3. 참가자 수 업데이트
            new_room.participant_count = 1
            
            # 변경사항 저장
            self.db.commit()
            self.db.refresh(new_room)
            self.db.refresh(participant)
            
            return new_room, participant
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def join_gameroom(self, room_id: int, guest_id: int) -> Optional[GameroomParticipant]:
        """
        게스트를 게임룸에 참가시킵니다.
        """
        try:
            # 게임룸 존재 여부 확인
            room = self.gameroom_repo.find_by_id(room_id)
            if not room or room.status != GameStatus.WAITING:
                return None
            
            # 이미 참가 중인지 확인
            existing = self.gameroom_repo.find_participant(room_id, guest_id)
            if existing:
                return existing
                
            # 정원 초과 확인
            if room.participant_count >= room.max_players:
                return None
            
            # 참가자 추가, 참가자 수 증가
            participant = self.gameroom_repo.add_participant(room_id, guest_id)

            self.db.commit()
            self.db.refresh(participant)
            return participant
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def leave_gameroom(self, room_id: int, guest_id: int) -> bool:
        """
        게스트가 게임룸을 떠납니다.
        """
        try:
            # 게임룸과 참가자 확인
            room = self.gameroom_repo.find_by_id(room_id)
            participant = self.gameroom_repo.find_participant(room_id, guest_id)
            
            if not room or not participant:
                return False
            
            # 참가자 제거
            self.gameroom_repo.remove_participant(room_id, guest_id)
            
            # 참가자 수 감소
            if room.participant_count > 0:
                room.participant_count -= 1
            
            # 방장이 나간 경우 처리
            if participant.is_creator:
                remaining = self.gameroom_repo.find_participants(room_id)
                if remaining:
                    # 다른 참가자 중 한 명을 방장으로 지정
                    new_host = remaining[0]
                    new_host.is_creator = True
                    # 상태도 READY로 변경
                    new_host.status = ParticipantStatus.READY
                else:
                    # 남은 참가자가 없으면 게임룸 종료
                    room.status = GameStatus.FINISHED
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def toggle_ready_status(self, room_id: int, guest_id: int) -> Optional[str]:
        """
        참가자의 준비 상태를 전환합니다.
        """
        try:
            participant = self.gameroom_repo.find_participant(room_id, guest_id)
            if not participant:
                return None
                
            # 방장은 항상 READY 상태
            if participant.is_creator:
                return ParticipantStatus.READY
                
            # 준비 상태 토글
            new_status = ParticipantStatus.WAITING
            if participant.status == ParticipantStatus.WAITING:
                new_status = ParticipantStatus.READY
                
            updated = self.gameroom_repo.update_participant_status(room_id, guest_id, new_status)
            return updated.status
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def start_game(self, room_id: int, host_id: int) -> bool:
        """
        게임을 시작합니다. 방장만 시작할 수 있습니다.
        """
        try:
            room = self.gameroom_repo.find_by_id(room_id)
            host = self.gameroom_repo.find_participant(room_id, host_id)
            
            # 게임룸과 방장 확인
            if not room or not host or not host.is_creator:
                return False
                
            # 게임 중이거나 종료된 경우
            if room.status != GameStatus.WAITING:
                return False
                
            # 모든 참가자가 준비 상태인지 확인
            participants = self.gameroom_repo.find_room_participants(room_id)
            all_ready = all(p.status == ParticipantStatus.READY or p.is_creator for p in participants)
            
            if not all_ready:
                return False
                
            # 게임 상태 변경
            room.status = GameStatus.PLAYING
            room.started_at = datetime.now()
            
            # 모든 참가자 상태를 PLAYING으로 변경
            for p in participants:
                p.status = ParticipantStatus.PLAYING
                
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def end_game(self, room_id: int) -> bool:
        """
        게임을 종료합니다.
        """
        try:
            room = self.gameroom_repo.find_by_id(room_id)
            if not room or room.status != GameStatus.PLAYING:
                return False
                
            room.status = GameStatus.FINISHED
            room.ended_at = datetime.now()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise e