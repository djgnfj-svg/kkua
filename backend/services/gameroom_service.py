from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import asyncio

from repositories.gameroom_repository import GameroomRepository
from models.gameroom_model import Gameroom, GameStatus, GameroomParticipant
from models.guest_model import Guest
from ws_manager.connection_manager import ConnectionManager
from repositories.guest_repository import GuestRepository
from repositories.gameroom_actions import GameroomActions

# 웹소켓 연결 관리자
ws_manager = ConnectionManager()


class GameroomService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = GameroomRepository(db)
        self.actions = GameroomActions(db)
        self.guest_repository = GuestRepository(db)

    def get_guest_by_cookie(self, request: Request) -> Guest:
        """쿠키에서 UUID를 추출하여 게스트를 반환합니다."""
        guest_uuid_str = request.cookies.get("kkua_guest_uuid")
        if not guest_uuid_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게스트 UUID가 필요합니다. 쿠키에 kkua_guest_uuid가 없습니다.",
            )

        try:
            guest_uuid = uuid.UUID(guest_uuid_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효하지 않은 UUID 형식입니다.",
            )

        guest = self.guest_repository.find_by_uuid(guest_uuid)
        if not guest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="유효하지 않은 게스트 UUID입니다.",
            )

        return guest

    def list_gamerooms(self, status=None, limit=10, offset=0):
        """게임룸 목록을 조회합니다. 정렬 기능을 제거했습니다."""
        # 상태 필터링 적용
        filter_args = {}
        if status:
            filter_args["status"] = status

        return self.repository.find_all(
            limit=limit, offset=offset, filter_args=filter_args
        )

    def get_gameroom(self, room_id: int) -> Optional[Gameroom]:
        """게임룸 상세 정보를 조회합니다."""
        return self.repository.find_by_id(room_id)

    def create_gameroom(
        self, data: Dict[str, Any], guest_id: int
    ) -> Optional[Gameroom]:
        """게임룸을 생성하고 방장을 자동으로 참가자로 추가합니다."""
        room, _ = self.actions.create_gameroom(data, guest_id)
        
        # 방장을 자동으로 참가자로 추가
        if room:
            self.repository.add_participant(room.room_id, guest_id)
            # 참가자 수 업데이트
            self.repository.update_participant_count(room.room_id)
            
        return room

    def update_gameroom(self, room_id: int, data: Dict[str, Any]) -> Optional[Gameroom]:
        """게임룸 정보를 업데이트합니다."""
        return self.repository.update(room_id, data)

    def delete_gameroom(self, room_id: int) -> bool:
        """게임룸을 삭제합니다."""
        return self.repository.delete(room_id)

    def join_gameroom(
        self, room_id: int, guest_id: int
    ) -> Optional[GameroomParticipant]:
        """게임룸에 참가합니다."""
        return self.actions.join_gameroom(room_id, guest_id)

    def leave_gameroom(self, room_id: int, guest_id: int) -> bool:
        """게임룸을 떠납니다."""
        return self.actions.leave_gameroom(room_id, guest_id)

    def toggle_ready_status(self, room_id: int, guest_id: int) -> Optional[str]:
        """준비 상태를 토글합니다."""
        return self.actions.toggle_ready_status(room_id, guest_id)

    def start_game(self, room_id: int, host_id: int) -> bool:
        """게임을 시작합니다."""
        return self.actions.start_game(room_id, host_id)

    def end_game(self, room_id: int) -> bool:
        """게임을 종료합니다."""
        return self.actions.end_game(room_id)

    def get_participants(self, room_id: int) -> List[Dict[str, Any]]:
        """게임룸 참가자 목록을 조회합니다."""
        return self.repository.get_participants(room_id)

    def update_participant_status(
        self, room_id: int, guest_id: int, status: str
    ) -> Dict[str, str]:
        """참가자 상태를 업데이트합니다. (웹소켓을 통해 호출)"""
        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸을 찾을 수 없습니다",
            )

        # 참가자 조회
        participant = self.repository.find_participant(room_id, guest_id)
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 참가자를 찾을 수 없습니다",
            )

        # 진행 중인 게임에서는 상태 변경 불가
        if room.status == GameStatus.PLAYING and status.upper() != "PLAYING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임 진행 중에는 상태를 변경할 수 없습니다",
            )

        # 상태 업데이트
        updated_participant = self.repository.update_participant_status(
            participant.id, status.upper()
        )

        # 웹소켓으로 상태 변경 알림 (ws_manager 유효성 검사 추가)
        if ws_manager:
            asyncio.create_task(
                ws_manager.broadcast_room_update(
                    room_id,
                    "status_changed",
                    {"guest_id": guest_id, "status": updated_participant.status.value},
                )
            )

        return {"detail": "참가자 상태가 업데이트되었습니다."}
