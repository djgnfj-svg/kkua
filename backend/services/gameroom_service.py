from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
import uuid

from repositories.gameroom_repository import GameroomRepository
from models.gameroom_model import Gameroom, GameStatus, GameroomParticipant, ParticipantStatus
from models.guest_model import Guest
from ws_manager.connection_manager import ConnectionManager
from repositories.guest_repository import GuestRepository
from services.game_state_service import GameStateService
from schemas.gameroom_actions_schema import JoinGameroomResponse

# 웹소켓 연결 관리자
ws_manager = ConnectionManager()


class GameroomService:
    """
    게임룸 관련 비즈니스 로직을 처리하는 서비스 클래스.
    
    게임룸 생성, 참가, 퇴장, 게임 시작/종료 등의 기능을 제공하며,
    실시간 웹소켓 알림 기능도 포함합니다.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = GameroomRepository(db)
        self.guest_repository = GuestRepository(db)
        self.game_state_service = GameStateService(db)
        self.ws_manager = ws_manager

    def get_guest_by_cookie(self, request: Request) -> Guest:
        """쿠키에서 게스트 UUID를 추출하고 게스트 정보를 반환합니다."""
        guest_uuid_str = request.cookies.get("kkua_guest_uuid")
        if not guest_uuid_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="게스트 UUID 쿠키가 없습니다.",
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
                detail="게스트를 찾을 수 없습니다.",
            )

        return guest

    def is_room_owner(self, room_id: int, guest_id: int) -> bool:
        """특정 게스트가 게임룸의 방장인지 확인합니다."""
        participant = self.repository.find_participant(room_id, guest_id)
        return participant is not None and participant.is_creator


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
        try:
            # 트랜잭션 시작
            # 1. 게임룸 생성
            room_data = data.copy()
            room_data["created_by"] = guest_id
            new_room = self.repository.create(room_data)

            # 2. 방장을 참가자로 추가 (참가자 수는 repository에서 자동 업데이트)
            self.repository.add_participant(
                room_id=new_room.room_id, guest_id=guest_id, is_creator=True
            )

            # 변경사항 저장
            self.db.commit()
            self.db.refresh(new_room)

            return new_room

        except Exception as e:
            self.db.rollback()
            raise e

    def update_gameroom(self, room_id: int, data: Dict[str, Any]) -> Optional[Gameroom]:
        """게임룸 정보를 업데이트합니다."""
        return self.repository.update(room_id, data)

    def delete_gameroom(self, room_id: int) -> bool:
        """게임룸을 삭제합니다."""
        return self.repository.delete(room_id)

    async def join_gameroom(
        self, room_id: int, guest: Guest
    ) -> JoinGameroomResponse:
        """
        게임룸에 참가합니다.
        
        Args:
            room_id: 참가할 게임룸 ID
            guest: 참가할 게스트 객체
            
        Returns:
            JoinGameroomResponse: 참가 결과 정보
            
        Raises:
            HTTPException: 게임룸이 존재하지 않거나 참가 불가능한 경우
        """
        try:
            # 게임룸 존재 여부 확인
            room = self.repository.find_by_id(room_id)
            if not room or room.status != GameStatus.WAITING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="게임룸 참가에 실패했습니다."
                )

            # 이미 참가 중인지 확인
            existing = self.repository.find_participant(room_id, guest.guest_id)
            if existing:
                return JoinGameroomResponse(
                    room_id=room_id, 
                    guest_id=guest.guest_id, 
                    message="이미 참가 중인 게임룸입니다."
                )

            # 정원 초과 확인
            if room.participant_count >= room.max_players:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="게임룸이 가득 찼습니다."
                )

            # 참가자 추가
            participant = self.repository.add_participant(room_id, guest.guest_id)
            
            self.db.commit()
            self.db.refresh(participant)

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
                room_id=room_id, 
                guest_id=guest.guest_id, 
                message="게임룸에 참가했습니다."
            )

        except Exception as e:
            self.db.rollback()
            raise e

    def leave_gameroom(self, room_id: int, guest: Guest) -> Dict[str, str]:
        """게임룸을 떠납니다."""
        try:
            # 게임룸과 참가자 확인
            room = self.repository.find_by_id(room_id)
            participant = self.repository.find_participant(room_id, guest.guest_id)

            if not room or not participant:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="게임룸 퇴장에 실패했습니다."
                )

            # 참가자 제거 (참가자 수는 repository에서 자동 업데이트)
            self.repository.remove_participant(room_id, guest.guest_id)

            # 방장이 나간 경우 처리
            if participant.is_creator:
                remaining = self.repository.find_room_participants(room_id)
                if remaining:
                    # 다른 참가자 중 한 명을 방장으로 지정
                    new_host = remaining[0]
                    new_host.is_creator = True
                    # 방장 이양 시 created_by 필드도 업데이트
                    room.created_by = new_host.guest_id
                    # 상태는 강제로 변경하지 않음 (기존 상태 유지)
                    
                    # 웹소켓으로 방장 변경 알림 전송
                    if self.ws_manager:
                        asyncio.create_task(
                            self.ws_manager.broadcast_room_update(
                                room_id,
                                "host_changed",
                                {
                                    "new_host_id": new_host.guest_id,
                                    "new_host_nickname": new_host.guest.nickname if new_host.guest else f"게스트_{new_host.guest_id}",
                                    "message": f"{new_host.guest.nickname if new_host.guest else f'게스트_{new_host.guest_id}'}님이 새로운 방장이 되었습니다.",
                                },
                            )
                        )
                else:
                    # 남은 참가자가 없으면 게임룸 종료
                    room.status = GameStatus.FINISHED

            self.db.commit()

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

        except Exception as e:
            self.db.rollback()
            raise e

    def toggle_ready_status(self, room_id: int, guest: Guest) -> Optional[str]:
        """준비 상태를 토글합니다."""
        try:
            participant = self.repository.find_participant(room_id, guest.guest_id)
            if not participant:
                return None

            # 방장은 항상 READY 상태
            if participant.is_creator:
                return ParticipantStatus.READY.value

            # 준비 상태 토글
            new_status = ParticipantStatus.WAITING
            if participant.status == ParticipantStatus.WAITING.value:
                new_status = ParticipantStatus.READY

            updated = self.repository.update_participant_status(
                room_id, participant.participant_id, new_status.value
            )
            return updated.status if updated else None

        except Exception as e:
            self.db.rollback()
            raise e

    def start_game(self, room_id: int, guest: Guest) -> Dict[str, str]:
        """게임을 시작합니다. 방장만 게임을 시작할 수 있습니다."""
        # 게임 시작 가능 여부 확인
        can_start, error_message = self.game_state_service.can_start_game(room_id, guest.guest_id)
        if not can_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # 게임 시작
        success = self.game_state_service.start_game(room_id)
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
        """게임을 종료하고 대기 상태로 되돌립니다."""
        success = self.game_state_service.end_game(room_id)
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
        if self.ws_manager:
            asyncio.create_task(
                self.ws_manager.broadcast_room_update(
                    room_id,
                    "status_changed",
                    {"guest_id": guest_id, "status": updated_participant.status.value},
                )
            )

        return {"detail": "참가자 상태가 업데이트되었습니다."}

    def toggle_ready_status_with_ws(self, room_id: int, guest: Guest) -> Dict[str, Any]:
        """참가자의 준비 상태를 토글합니다. (웹소켓 알림 포함)"""
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
        if self.is_room_owner(room_id, guest.guest_id):
            return {
                "status": ParticipantStatus.READY.value,
                "message": "방장은 항상 준비 상태입니다.",
                "is_ready": True,
            }

        # 현재 상태 확인 및 새 상태 설정
        current_status = participant.status
        
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

        # 웹소켓 이벤트 발송 (참가자 상태 변경)
        print(f"🔄 준비 상태 변경: room_id={room_id}, guest_id={guest.guest_id}, is_ready={is_ready}")
        if self.ws_manager:
            print(f"📡 WebSocket 알림 전송 중...")
            asyncio.create_task(
                self.ws_manager.broadcast_ready_status(
                    room_id, guest.guest_id, is_ready, guest.nickname
                )
            )
        else:
            print(f"❌ WebSocket 관리자가 없습니다!")

        return {"status": new_status, "message": message, "is_ready": is_ready}

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
            is_owner = self.is_room_owner(room_id, guest.guest_id)

            return {"is_owner": is_owner}
        except HTTPException:
            return {"is_owner": False}
