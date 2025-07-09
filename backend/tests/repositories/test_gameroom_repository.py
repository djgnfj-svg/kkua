import uuid

from sqlalchemy.orm import Session

from repositories.gameroom_repository import GameroomRepository
from repositories.guest_repository import GuestRepository
from models.gameroom_model import GameStatus, GameroomParticipant, ParticipantStatus


class TestGameroomRepository:
    def test_create_gameroom(self, db_session: Session):
        """게임룸 생성 테스트"""
        # 게스트 생성
        guest_repo = GuestRepository(db_session)
        guest = guest_repo.create(uuid.uuid4(), "방생성테스트")

        # 게임룸 리포지토리 인스턴스
        repo = GameroomRepository(db_session)

        # 게임룸 생성
        room_data = {
            "title": "테스트 게임룸",
            "max_players": 10,
            "game_mode": "test",
            "created_by": guest.guest_id,
        }

        room = repo.create(room_data)

        # 검증
        assert room.room_id is not None
        assert room.title == "테스트 게임룸"
        assert room.max_players == 10
        assert room.game_mode == "test"
        assert room.created_by == guest.guest_id
        assert room.status == GameStatus.WAITING.value
        assert room.participant_count == 0

    def test_find_by_id(self, db_session: Session):
        """ID로 게임룸 조회 테스트"""
        # 게스트 생성
        guest_repo = GuestRepository(db_session)
        guest = guest_repo.create(uuid.uuid4(), "조회테스트")

        # 게임룸 리포지토리 인스턴스
        repo = GameroomRepository(db_session)

        # 게임룸 생성
        room_data = {"title": "ID 조회 테스트", "created_by": guest.guest_id}

        created_room = repo.create(room_data)

        # ID로 조회
        found_room = repo.find_by_id(created_room.room_id)

        # 검증
        assert found_room is not None
        assert found_room.room_id == created_room.room_id
        assert found_room.title == "ID 조회 테스트"

    def test_add_participant(self, db_session: Session):
        """참가자 추가 테스트"""
        # 게스트 생성
        guest_repo = GuestRepository(db_session)
        guest = guest_repo.create(uuid.uuid4(), "참가자")

        # 게임룸 리포지토리 인스턴스
        repo = GameroomRepository(db_session)

        # 게임룸 생성
        room_data = {"title": "참가자 테스트", "created_by": guest.guest_id}

        room = repo.create(room_data)

        # 참가자 추가
        participant = repo.add_participant(
            room.room_id, guest.guest_id, is_creator=True
        )

        # 검증
        assert participant is not None
        assert participant.room_id == room.room_id
        assert participant.guest_id == guest.guest_id
        assert participant.is_creator is True
        assert participant.status == ParticipantStatus.READY.value

        # 게임룸의 참가자 수 확인
        room = repo.find_by_id(room.room_id)
        assert room.participant_count == 1

    def test_find_participant(self, db_session: Session):
        """참가자 조회 테스트"""
        # 게스트 생성
        guest_repo = GuestRepository(db_session)
        guest = guest_repo.create(uuid.uuid4(), "참가자조회")

        # 게임룸 리포지토리 인스턴스
        repo = GameroomRepository(db_session)

        # 게임룸 생성
        room_data = {"title": "참가자 조회 테스트", "created_by": guest.guest_id}

        room = repo.create(room_data)

        # 참가자 추가
        created_participant = repo.add_participant(room.room_id, guest.guest_id)

        # 참가자 조회
        found_participant = repo.find_participant(room.room_id, guest.guest_id)

        # 검증
        assert found_participant is not None
        assert found_participant.participant_id == created_participant.participant_id

    def test_remove_participant(self, db_session: Session):
        """참가자 제거 테스트"""
        # 게스트 생성
        guest_repo = GuestRepository(db_session)
        guest = guest_repo.create(uuid.uuid4(), "퇴장테스트")

        # 게임룸 리포지토리 인스턴스
        repo = GameroomRepository(db_session)

        # 게임룸 생성
        room_data = {"title": "퇴장 테스트", "created_by": guest.guest_id}

        room = repo.create(room_data)

        # 참가자 추가
        repo.add_participant(room.room_id, guest.guest_id)

        # 참가자 제거
        result = repo.remove_participant(room.room_id, guest.guest_id)

        # 검증
        assert result is True

        # 참가자가 LEFT 상태로 변경되었는지 확인 (완전히 삭제되지는 않음)
        participant = (
            db_session.query(GameroomParticipant)
            .filter(
                GameroomParticipant.room_id == room.room_id,
                GameroomParticipant.guest_id == guest.guest_id,
            )
            .first()
        )

        assert participant is not None
        assert participant.status == ParticipantStatus.LEFT
        assert participant.left_at is not None

    def test_update_game_status(self, db_session: Session):
        """게임 상태 업데이트 테스트"""
        # 게스트 생성
        guest_repo = GuestRepository(db_session)
        guest = guest_repo.create(uuid.uuid4(), "상태테스트")

        # 게임룸 리포지토리 인스턴스
        repo = GameroomRepository(db_session)

        # 게임룸 생성
        room_data = {"title": "상태 테스트", "created_by": guest.guest_id}

        room = repo.create(room_data)

        # 참가자 추가
        repo.add_participant(room.room_id, guest.guest_id)

        # 게임 상태 변경 (WAITING -> PLAYING)
        updated_room = repo.update_game_status(room, GameStatus.PLAYING)

        # 검증
        assert updated_room.status == GameStatus.PLAYING.value

        # 참가자 상태도 변경되었는지 확인
        participant = repo.find_participant(room.room_id, guest.guest_id)
        assert participant.status == ParticipantStatus.PLAYING.value
