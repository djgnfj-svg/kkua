from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from repositories.gameroom_repository import GameroomRepository
from models.gameroom_model import Gameroom, GameStatus, GameroomParticipant, ParticipantStatus
from models.guest_model import Guest
from ws_manager.connection_manager import ConnectionManager
from repositories.guest_repository import GuestRepository

# 웹소켓 연결 관리자
ws_manager = ConnectionManager()


class GameroomService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = GameroomRepository(db)
        self.guest_repository = GuestRepository(db)


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

            # 2. 방장을 참가자로 추가
            self.repository.add_participant(
                room_id=new_room.room_id, guest_id=guest_id, is_creator=True
            )

            # 3. 참가자 수 업데이트
            new_room.participant_count = 1

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

    def join_gameroom(
        self, room_id: int, guest_id: int
    ) -> Optional[GameroomParticipant]:
        """게임룸에 참가합니다."""
        try:
            # 게임룸 존재 여부 확인
            room = self.repository.find_by_id(room_id)
            if not room or room.status != GameStatus.WAITING:
                return None

            # 이미 참가 중인지 확인
            existing = self.repository.find_participant(room_id, guest_id)
            if existing:
                return existing

            # 정원 초과 확인
            if room.participant_count >= room.max_players:
                return None

            # 참가자 추가, 참가자 수 증가
            participant = self.repository.add_participant(room_id, guest_id)

            self.db.commit()
            self.db.refresh(participant)
            return participant

        except Exception as e:
            self.db.rollback()
            raise e

    def leave_gameroom(self, room_id: int, guest_id: int) -> bool:
        """게임룸을 떠납니다."""
        try:
            # 게임룸과 참가자 확인
            room = self.repository.find_by_id(room_id)
            participant = self.repository.find_participant(room_id, guest_id)

            if not room or not participant:
                return False

            # 참가자 제거
            self.repository.remove_participant(room_id, guest_id)

            # 참가자 수 감소
            if room.participant_count > 0:
                room.participant_count -= 1

            # 방장이 나간 경우 처리
            if participant.is_creator:
                remaining = self.repository.find_room_participants(room_id)
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
        """준비 상태를 토글합니다."""
        try:
            participant = self.repository.find_participant(room_id, guest_id)
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

    def start_game(self, room_id: int, host_id: int) -> bool:
        """게임을 시작합니다. 방장만 시작할 수 있습니다."""
        try:
            room = self.repository.find_by_id(room_id)
            host = self.repository.find_participant(room_id, host_id)

            # 게임룸과 방장 확인
            if not room or not host or not host.is_creator:
                return False

            # 게임 중이거나 종료된 경우
            if room.status != GameStatus.WAITING:
                return False

            # 모든 참가자가 준비 상태인지 확인
            participants = self.repository.find_room_participants(room_id)
            all_ready = all(
                p.status == ParticipantStatus.READY.value or p.is_creator
                for p in participants
            )

            if not all_ready:
                return False

            # 게임 상태 변경
            room.status = GameStatus.PLAYING
            room.started_at = datetime.now()

            # 모든 참가자 상태를 PLAYING으로 변경
            for p in participants:
                p.status = ParticipantStatus.PLAYING.value

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            raise e

    def end_game(self, room_id: int) -> bool:
        """게임을 종료합니다."""
        try:
            room = self.repository.find_by_id(room_id)
            if not room or room.status != GameStatus.PLAYING:
                return False

            room.status = GameStatus.FINISHED
            room.ended_at = datetime.now()

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            raise e

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
