from fastapi import HTTPException, status
from typing import List, Dict, Any
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

from services.gameroom_service import GameroomService, ws_manager
from models.gameroom_model import GameStatus, ParticipantStatus
from models.guest_model import Guest
from schemas.gameroom_actions_schema import JoinGameroomResponse


class GameroomActionsService:
    def __init__(self, db: Session):
        self.db = db
        self.gameroom_service = GameroomService(db)
        self.ws_manager = ws_manager

    def join_gameroom(self, room_id: int, guest: Guest) -> JoinGameroomResponse:
        """게임룸에 참가합니다."""
        # GameroomService의 기능 사용
        participant = self.gameroom_service.join_gameroom(room_id, guest.guest_id)
        
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임룸 참가에 실패했습니다."
            )

        # 웹소켓 이벤트 발송 (게임룸 참가 알림)
        if self.ws_manager:
            asyncio.create_task(
                self.ws_manager.broadcast_room_update(
                    room_id,
                    "player_joined",
                    {
                        "guest_id": guest.guest_id,
                        "nickname": guest.nickname,
                        "joined_at": datetime.now().isoformat(),
                        "is_creator": False,
                    },
                )
            )

        return JoinGameroomResponse(
            room_id=room_id, guest_id=guest.guest_id, message="게임룸에 참가했습니다."
        )

    def leave_gameroom(self, room_id: int, guest: Guest) -> Dict[str, str]:
        """게임룸에서 나갑니다."""
        # GameroomService의 기능 사용
        success = self.gameroom_service.leave_gameroom(room_id, guest.guest_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임룸 퇴장에 실패했습니다."
            )

        # 웹소켓 이벤트 발송 (참가자 퇴장)
        if self.ws_manager:
            asyncio.create_task(
                self.ws_manager.broadcast_room_update(
                    room_id,
                    "player_left",
                    {
                        "guest_id": guest.guest_id,
                        "nickname": guest.nickname,
                        "left_at": datetime.now().isoformat(),
                    },
                )
            )

        return {"message": "게임룸에서 퇴장했습니다."}

    def start_game(self, room_id: int, guest: Guest) -> Dict[str, str]:
        """게임을 시작합니다. 방장만 게임을 시작할 수 있습니다."""
        # GameroomService의 기능 사용
        success = self.gameroom_service.start_game(room_id, guest.guest_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임 시작에 실패했습니다."
            )

        # 웹소켓 이벤트 발송 (게임 시작)
        if self.ws_manager:
            asyncio.create_task(
                self.ws_manager.broadcast_room_update(
                    room_id,
                    "game_started",
                    {
                        "room_id": room_id,
                        "started_at": datetime.now().isoformat(),
                        "message": "게임이 시작되었습니다!",
                    },
                )
            )

        return {"message": "게임이 시작되었습니다!", "status": "PLAYING"}

    def end_game(self, room_id: int, guest: Guest) -> Dict[str, str]:
        """게임을 종료하고 대기 상태로 되돌립니다. 방장만 게임을 종료할 수 있습니다."""
        # GameroomService의 기능 사용
        success = self.gameroom_service.end_game(room_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임 종료에 실패했습니다."
            )

        # 웹소켓 이벤트 발송 (게임 종료)
        if self.ws_manager:
            asyncio.create_task(
                self.ws_manager.broadcast_room_update(
                    room_id,
                    "game_ended",
                    {
                        "room_id": room_id,
                        "ended_at": datetime.now().isoformat(),
                        "message": "게임이 종료되었습니다! 다시 준비해주세요.",
                    },
                )
            )

        return {
            "message": "게임이 종료되었습니다! 다시 준비해주세요.",
            "status": "WAITING",
        }

    def get_participants(self, room_id: int) -> List[Dict[str, Any]]:
        """게임룸의 참가자 목록을 조회합니다."""
        return self.gameroom_service.get_participants(room_id)

    def check_active_game(self, guest_uuid_str: str = None) -> Dict[str, Any]:
        """유저가 현재 참여 중인 게임이 있는지 확인합니다."""
        if guest_uuid_str:
            # URL 파라미터로 UUID가 제공된 경우
            try:
                guest_uuid = uuid.UUID(guest_uuid_str)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="유효하지 않은 UUID 형식입니다.",
                )
        else:
            return {"has_active_game": False, "room_id": None}

        # UUID로 게스트 조회
        guest = self.guest_repository.find_by_uuid(guest_uuid)
        if not guest:
            return {"has_active_game": False, "room_id": None}

        # 활성화된 게임 확인
        should_redirect, active_room_id = self.guest_repository.check_active_game(
            guest.guest_id
        )

        return {"has_active_game": should_redirect, "room_id": active_room_id}

    def check_if_owner(self, room_id: int, guest: Guest) -> Dict[str, bool]:
        """현재 게스트가 특정 게임룸의 방장인지 확인합니다."""
        try:
            # 게임룸 조회
            room = self.repository.find_by_id(room_id)
            if not room:
                return {"is_owner": False}

            # 방장 여부 확인
            is_owner = room.created_by == guest.guest_id

            return {"is_owner": is_owner}
        except HTTPException:
            return {"is_owner": False}

    def toggle_ready_status(self, room_id: int, guest: Guest) -> Dict[str, Any]:
        """참가자의 준비 상태를 토글합니다."""

        # 게임룸 조회
        room = self.repository.find_by_id(room_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게임룸이 존재하지 않습니다.",
            )

        # 참가자 조회
        participant = self.repository.find_participant(room_id, guest.guest_id)
        if not participant or participant.left_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="해당 게임룸에 참가 중이 아닙니다.",
            )

        # 게임 상태 확인
        if room.status != GameStatus.WAITING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="대기 중인 게임방에서만 준비 상태를 변경할 수 있습니다.",
            )

        # 방장 확인 - 방장은 항상 준비 상태
        is_creator = room.created_by == guest.guest_id
        if is_creator:
            return {
                "status": ParticipantStatus.READY.value,
                "message": "방장은 항상 준비 상태입니다.",
                "is_ready": True,
            }

        # 현재 상태 확인 및 새 상태 설정
        current_status = participant.status
        print(f"현재 참가자 상태: {current_status}")

        new_status = None
        if (
            current_status == ParticipantStatus.WAITING.value
            or current_status == ParticipantStatus.WAITING
        ):
            new_status = ParticipantStatus.READY.value
            is_ready = True
            message = "준비 완료!"
        else:
            new_status = ParticipantStatus.WAITING.value
            is_ready = False
            message = "준비 취소!"

        # 상태 업데이트
        result = self.repository.update_participant_status(
            room.room_id, participant.participant_id, new_status
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="참가자 상태 업데이트에 실패했습니다.",
            )

        print(f"참가자 상태 업데이트 완료: {current_status} -> {new_status}")

        # 웹소켓 이벤트 발송 (참가자 상태 변경)
        if self.ws_manager:
            asyncio.create_task(
                self.ws_manager.broadcast_room_update(
                    room_id,
                    "player_ready_changed",
                    {
                        "guest_id": guest.guest_id,
                        "nickname": guest.nickname,
                        "status": new_status,
                        "is_ready": is_ready,
                    },
                )
            )

        return {"status": new_status, "message": message, "is_ready": is_ready}