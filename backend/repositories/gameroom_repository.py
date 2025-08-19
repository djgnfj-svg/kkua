from sqlalchemy.orm import Session
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy import text
import logging

from models.gameroom_model import (
    Gameroom,
    GameStatus,
    GameroomParticipant,
    ParticipantStatus,
)

logger = logging.getLogger(__name__)


class GameroomRepository:
    """간소화된 게임룸 레포지토리 - 핵심 CRUD 기능만 포함"""

    def __init__(self, db: Session):
        self.db = db

    # ============ Core CRUD Operations ============

    def find_by_id(self, room_id: int) -> Optional[Gameroom]:
        """ID로 게임룸을 찾습니다."""
        return self.db.query(Gameroom).filter(Gameroom.room_id == room_id).first()

    def create(self, data: Dict[str, Any]) -> Gameroom:
        """게임룸을 생성합니다."""
        now = datetime.now()

        new_room = Gameroom(
            title=data.get("title", "새 게임"),
            max_players=data.get("max_players", 8),
            game_mode=data.get("game_mode", "standard"),
            time_limit=data.get("time_limit", 300),
            status=GameStatus.WAITING,
            created_by=data.get("created_by"),
            created_at=now,
            updated_at=now,
            participant_count=0,
            room_type=data.get("room_type", "normal"),
        )

        self.db.add(new_room)
        self.db.flush()  # room_id를 얻기 위해 flush
        return new_room

    def update(self, room_id: int, data: Dict[str, Any]) -> Optional[Gameroom]:
        """게임룸을 업데이트합니다."""
        room = self.find_by_id(room_id)
        if not room:
            return None

        # 값이 제공된 경우에만 업데이트
        for key, value in data.items():
            if hasattr(room, key) and value is not None:
                setattr(room, key, value)

        room.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(room)
        return room

    def delete(self, room_id: int) -> bool:
        """게임룸을 삭제합니다 (상태를 FINISHED로 변경)."""
        room = self.find_by_id(room_id)
        if not room:
            return False

        room.status = GameStatus.FINISHED
        self.db.commit()
        return True

    def find_all(
        self, limit=10, offset=0, filter_args=None
    ) -> Tuple[List[Gameroom], int]:
        """모든 게임룸을 조회합니다 (생성자 정보 포함, 최적화된 쿼리)."""
        from sqlalchemy.orm import joinedload

        query = self.db.query(Gameroom).options(joinedload(Gameroom.creator))

        # 필터링 적용 (인덱스 활용)
        if filter_args:
            for key, value in filter_args.items():
                if hasattr(Gameroom, key) and value is not None:
                    if key == "status":
                        # 상태별 필터링 (인덱스 활용)
                        query = query.filter(Gameroom.status == value)
                    else:
                        query = query.filter(getattr(Gameroom, key) == value)

        # 총 개수 계산 (최적화된 카운트 쿼리)
        count_query = self.db.query(Gameroom.room_id)
        if filter_args:
            for key, value in filter_args.items():
                if hasattr(Gameroom, key) and value is not None:
                    count_query = count_query.filter(getattr(Gameroom, key) == value)
        total = count_query.count()

        # 기본 정렬: 생성일시 기준 내림차순 (인덱스 활용)
        query = query.order_by(Gameroom.created_at.desc())

        # 페이지네이션 적용
        rooms = query.offset(offset).limit(limit).all()
        return rooms, total

    # ============ Participant Management ============

    def find_participant(
        self, room_id: int, guest_id: int
    ) -> Optional[GameroomParticipant]:
        """방 ID와 게스트 ID로 특정 참가자를 찾습니다 (활성 참가자만)."""
        return (
            self.db.query(GameroomParticipant)
            .filter(
                GameroomParticipant.room_id == room_id,
                GameroomParticipant.guest_id == guest_id,
                GameroomParticipant.left_at.is_(None),  # 활성 참가자만
            )
            .first()
        )

    def find_room_participants(self, room_id: int) -> List[GameroomParticipant]:
        """특정 게임룸의 모든 활성 참가자를 조회합니다 (Guest 정보 포함, N+1 쿼리 방지)."""
        from sqlalchemy.orm import joinedload

        return (
            self.db.query(GameroomParticipant)
            .options(joinedload(GameroomParticipant.guest))  # N+1 쿼리 방지
            .filter(
                GameroomParticipant.room_id == room_id,
                GameroomParticipant.left_at.is_(None),
            )
            .order_by(GameroomParticipant.joined_at)
            .all()
        )

    def add_participant(
        self, room_id: int, guest_id: int, is_creator: bool = False
    ) -> Optional[GameroomParticipant]:
        """게임룸에 참가자를 추가합니다."""
        participant = GameroomParticipant(
            room_id=room_id,
            guest_id=guest_id,
            joined_at=datetime.now(),
            status=ParticipantStatus.READY.value
            if is_creator
            else ParticipantStatus.WAITING.value,
            is_creator=is_creator,
        )

        self.db.add(participant)
        self.db.flush()

        # 참가자 수 업데이트
        self.update_participant_count(room_id)

        return participant

    def remove_participant(self, room_id: int, guest_id: int) -> bool:
        """게임룸에서 참가자를 제거합니다 (soft delete)."""
        participant = self.find_participant(room_id, guest_id)
        if not participant:
            return False

        participant.left_at = datetime.now()
        participant.status = ParticipantStatus.LEFT.value

        # 참가자 수 업데이트
        self.update_participant_count(room_id)

        self.db.commit()
        return True

    def update_participant_status(self, room_id: int, participant_id: int, status: str):
        """참가자의 상태를 업데이트합니다."""
        participant = (
            self.db.query(GameroomParticipant)
            .filter(GameroomParticipant.participant_id == participant_id)
            .first()
        )

        if not participant:
            return False

        participant.status = status
        participant.updated_at = datetime.now()
        self.db.commit()
        return participant

    def get_participants(self, room_id: int) -> List[Dict[str, Any]]:
        """게임룸 참여자 목록을 가져옵니다."""
        gameroom = self.find_by_id(room_id)
        if not gameroom:
            return []

        # 참가자 정보 조회 쿼리 (status와 is_ready 필드 포함)
        query = """
            SELECT gp.guest_id, g.nickname, gp.joined_at, gp.is_creator, gp.status
            FROM gameroom_participants gp
            JOIN guests g ON gp.guest_id = g.guest_id
            WHERE gp.room_id = :room_id AND gp.left_at IS NULL
            ORDER BY gp.joined_at ASC
        """

        try:
            result = self.db.execute(text(query), {"room_id": room_id}).fetchall()

            # 결과를 딕셔너리 리스트로 변환
            participants = [
                {
                    "guest_id": row[0],
                    "nickname": row[1],
                    "is_creator": bool(row[3]),  # is_creator 필드 사용
                    "joined_at": row[2],
                    "status": row[4],  # status 필드 추가
                    "is_ready": row[4].lower()
                    == "ready",  # status 기반으로 is_ready 계산
                }
                for row in result
            ]

            # 생성자가 먼저 오도록 정렬
            participants.sort(key=lambda p: (not p["is_creator"], p["joined_at"]))
            return participants

        except Exception as e:
            logger.error(f"참가자 목록 조회 오류: {str(e)}")
            return []

    def update_participant_count(self, room_id: int) -> bool:
        """게임룸의 참가자 수를 업데이트합니다."""
        try:
            # 현재 활성 참가자 수 계산
            count_query = """
                SELECT COUNT(*) FROM gameroom_participants
                WHERE room_id = :room_id AND left_at IS NULL
            """
            count = self.db.execute(text(count_query), {"room_id": room_id}).scalar()

            # 게임룸 정보 조회
            room = self.find_by_id(room_id)
            if not room:
                return False

            # 참가자 수 업데이트
            room.participant_count = count
            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"참가자 수 업데이트 오류: {str(e)}")
            return False

    def is_room_creator(self, room_id: int, guest_id: int) -> bool:
        """특정 게스트가 해당 방의 방장인지 확인합니다."""
        try:
            room = self.find_by_id(room_id)
            return room is not None and room.created_by == guest_id
        except Exception as e:
            logger.error(f"방장 확인 오류: {str(e)}")
            return False

    def kick_participant(self, room_id: int, target_guest_id: int, kicker_guest_id: int) -> bool:
        """참가자를 강퇴합니다."""
        try:
            # 강퇴하는 사람이 방장인지 확인
            if not self.is_room_creator(room_id, kicker_guest_id):
                logger.warning(f"권한 없음: {kicker_guest_id}는 방 {room_id}의 방장이 아님")
                return False

            # 자기 자신은 강퇴할 수 없음
            if target_guest_id == kicker_guest_id:
                logger.warning(f"자기 자신 강퇴 시도: {kicker_guest_id}")
                return False

            # 참가자 찾기
            participant = self.find_participant(room_id, target_guest_id)
            if not participant or participant.left_at is not None:
                logger.warning(f"참가자 없음 또는 이미 나감: room_id={room_id}, guest_id={target_guest_id}")
                return False

            # 방장 자신은 강퇴 불가 (추가 보안)
            if participant.is_creator:
                logger.warning(f"방장 강퇴 시도: {target_guest_id}")
                return False

            # 강퇴 처리: left_at 시간 설정, 상태를 LEFT로 변경
            participant.left_at = datetime.now()
            participant.status = ParticipantStatus.LEFT

            self.db.commit()
            
            # 참가자 수 업데이트
            self.update_participant_count(room_id)
            
            logger.info(f"강퇴 완료: room_id={room_id}, target={target_guest_id}, kicker={kicker_guest_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"강퇴 처리 오류: {str(e)}")
            return False
