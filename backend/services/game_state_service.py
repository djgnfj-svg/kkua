from sqlalchemy.orm import Session
from typing import Optional
import logging
from datetime import datetime

from repositories.gameroom_repository import GameroomRepository
from models.gameroom_model import Gameroom, GameStatus, ParticipantStatus


class GameStateService:
    """게임 상태 관리 전담 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = GameroomRepository(db)
        self.logger = logging.getLogger(__name__)

    def start_game(self, room_id: int) -> bool:
        """게임을 시작 상태로 변경합니다."""
        try:
            # 게임룸 조회
            room = self.repository.find_by_id(room_id)
            if not room:
                return False

            # 게임 상태 변경
            room.status = GameStatus.PLAYING
            room.started_at = datetime.now()
            room.updated_at = datetime.now()

            # 모든 참가자 상태를 PLAYING으로 변경
            participants = self.repository.find_room_participants(room_id)
            for participant in participants:
                participant.status = ParticipantStatus.PLAYING.value
                participant.updated_at = datetime.now()

            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"게임 시작 오류: {str(e)}", exc_info=True)
            return False

    def end_game(self, room_id: int) -> bool:
        """게임을 종료 상태로 변경하고 참가자들은 대기 상태로 되돌립니다."""
        try:
            # 게임룸 조회
            room = self.repository.find_by_id(room_id)
            if not room:
                return False

            # 게임룸 상태를 WAITING으로 변경 (새 게임을 위해)
            room.status = GameStatus.WAITING
            room.ended_at = datetime.now()
            room.updated_at = datetime.now()

            # 모든 참가자 상태를 WAITING으로 변경
            participants = self.repository.find_room_participants(room_id)
            for participant in participants:
                # 방장은 항상 READY 상태로, 나머지는 WAITING으로
                if participant.is_creator:
                    participant.status = ParticipantStatus.READY.value
                else:
                    participant.status = ParticipantStatus.WAITING.value
                participant.updated_at = datetime.now()

            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"게임 종료 오류: {str(e)}", exc_info=True)
            return False

    def check_all_ready(self, room_id: int) -> bool:
        """모든 참가자가 준비 상태인지 확인합니다."""
        try:
            # 방장 정보 조회
            room = self.repository.find_by_id(room_id)
            if not room:
                return False

            creator_id = room.created_by

            # 참가자 조회 (방장 제외)
            participants = self.repository.find_room_participants(room_id)
            non_creator_participants = [p for p in participants if p.guest_id != creator_id]

            # 참가자가 없으면 시작 불가
            if not non_creator_participants:
                return False

            # 모든 참가자가 READY 상태인지 확인
            all_ready = all(
                p.status == ParticipantStatus.READY.value for p in non_creator_participants
            )

            return all_ready
            
        except Exception as e:
            self.logger.error(f"준비 상태 확인 오류: {str(e)}", exc_info=True)
            return False
    
    def can_start_game(self, room_id: int, host_id: int) -> tuple[bool, str]:
        """게임 시작 가능 여부를 확인합니다. (성공 여부, 에러 메시지) 반환"""
        room = self.repository.find_by_id(room_id)
        if not room:
            return False, "존재하지 않는 방입니다."
            
        # 방장 확인
        if room.created_by != host_id:
            return False, "방장만 게임을 시작할 수 있습니다."
            
        # 게임 상태 확인
        if room.status != GameStatus.WAITING:
            if room.status == GameStatus.PLAYING:
                return False, "이미 게임이 진행 중입니다."
            else:
                return False, "게임을 시작할 수 없는 방 상태입니다."
            
        # 최소 인원 확인
        participants = self.repository.find_room_participants(room_id)
        if len(participants) < 2:
            return False, "게임 시작을 위해 최소 2명의 플레이어가 필요합니다."
            
        # 모든 참가자 준비 상태 확인
        if not self.check_all_ready(room_id):
            return False, "모든 플레이어가 준비 상태여야 합니다."
            
        return True, "게임 시작 가능"
    
    def can_end_game(self, room_id: int, host_id: int) -> bool:
        """게임 종료 가능 여부를 확인합니다."""
        room = self.repository.find_by_id(room_id)
        if not room:
            return False
            
        # 방장 확인
        if room.created_by != host_id:
            return False
            
        # 게임 상태 확인
        return room.status == GameStatus.PLAYING