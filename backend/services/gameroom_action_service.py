"""
Gameroom Action Service - 게임룸 액션 (참가, 나가기, 준비 등) 전담
"""

from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

from models.guest_model import Guest
from models.gameroom_model import GameroomParticipant, ParticipantStatus
from repositories.gameroom_repository import GameroomRepository
from services.room_state_manager import get_room_state_manager
from schemas.gameroom_actions_schema import JoinGameroomResponse


class GameroomActionService:
    """게임룸 액션 처리 전담 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = GameroomRepository(db)
        self.room_state_manager = get_room_state_manager()
    
    def join_gameroom(self, room_id: int, guest: Guest) -> JoinGameroomResponse:
        """게임룸에 참가합니다."""
        # 동시성 제어를 통한 안전한 참가 처리
        success, message, participant = self.room_state_manager.join_room_atomically(
            self.db, room_id, guest
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return JoinGameroomResponse(
            room_id=room_id,
            guest_id=guest.guest_id,
            nickname=guest.nickname,
            joined_at=participant.joined_at.isoformat() if participant.joined_at else None,
            status=participant.status,
            is_creator=participant.is_creator,
            message=message
        )
    
    def leave_gameroom(self, room_id: int, guest: Guest) -> Dict[str, str]:
        """게임룸에서 나갑니다."""
        success, message = self.room_state_manager.leave_room_atomically(
            self.db, room_id, guest
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return {"message": message}
    
    def toggle_ready_status(self, room_id: int, guest: Guest) -> Dict[str, Any]:
        """참가자의 준비 상태를 토글합니다."""
        try:
            # 참가자 정보 확인
            participant = self.repository.find_participant(room_id, guest.guest_id)
            if not participant or participant.left_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="해당 게임룸에 참가 중이 아닙니다."
                )
            
            # 방장은 항상 준비 상태
            if participant.is_creator:
                return {
                    "status": ParticipantStatus.READY.value,
                    "message": "방장은 항상 준비 상태입니다.",
                    "is_ready": True,
                }
            
            # 현재 상태에 따라 토글
            current_status = participant.status
            if current_status == ParticipantStatus.WAITING.value:
                new_status = ParticipantStatus.READY.value
                is_ready = True
                message = "준비 완료!"
            else:
                new_status = ParticipantStatus.WAITING.value
                is_ready = False
                message = "준비 취소!"
            
            # 상태 업데이트
            result = self.repository.update_participant_status(
                room_id, participant.participant_id, new_status
            )
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="참가자 상태 업데이트에 실패했습니다."
                )
            
            self.db.commit()
            
            return {
                "status": new_status,
                "message": message,
                "is_ready": is_ready,
            }
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"준비 상태 변경 실패: {str(e)}"
            )
    
    def get_participants(self, room_id: int) -> Dict[str, Any]:
        """게임룸의 참가자 목록을 조회합니다."""
        participants = self.repository.find_room_participants(room_id)
        
        participant_list = []
        for p in participants:
            participant_info = {
                "guest_id": p.guest_id,
                "nickname": p.guest.nickname if p.guest else f"게스트_{p.guest_id}",
                "status": p.status,
                "is_creator": p.is_creator,
                "joined_at": p.joined_at.isoformat() if p.joined_at else None,
                "is_ready": p.status == ParticipantStatus.READY.value
            }
            participant_list.append(participant_info)
        
        return {
            "room_id": room_id,
            "participants": participant_list,
            "total_count": len(participant_list)
        }
    
    def check_if_owner(self, room_id: int, guest: Guest) -> Dict[str, bool]:
        """현재 게스트가 특정 게임룸의 방장인지 확인합니다."""
        participant = self.repository.find_participant(room_id, guest.guest_id)
        is_owner = (
            participant is not None 
            and participant.left_at is None 
            and participant.is_creator
        )
        
        return {"is_owner": is_owner}
    
    def check_active_game(self, guest_uuid_str: str = None) -> Dict[str, Any]:
        """유저가 현재 참여 중인 게임이 있는지 확인합니다."""
        if not guest_uuid_str:
            return {"has_active_game": False, "room_id": None}
        
        try:
            from uuid import UUID
            guest_uuid = UUID(guest_uuid_str)
            
            # UUID로 게스트 찾기
            from repositories.guest_repository import GuestRepository
            guest_repo = GuestRepository(self.db)
            guest = guest_repo.find_by_uuid(guest_uuid)
            
            if not guest:
                return {"has_active_game": False, "room_id": None}
            
            # 활성 게임 확인
            has_active_game, room_id = guest_repo.check_active_game(guest.guest_id)
            
            return {
                "has_active_game": has_active_game,
                "room_id": room_id,
                "guest_id": guest.guest_id
            }
            
        except ValueError:
            return {"has_active_game": False, "room_id": None, "error": "Invalid UUID format"}
        except Exception as e:
            return {"has_active_game": False, "room_id": None, "error": str(e)}