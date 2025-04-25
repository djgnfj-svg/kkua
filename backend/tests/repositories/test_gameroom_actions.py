import pytest
import uuid
from sqlalchemy.orm import Session

from repositories.gameroom_actions import GameroomActions
from repositories.guest_repository import GuestRepository
from models.gameroom_model import Gameroom, GameStatus, GameroomParticipant, ParticipantStatus

class TestGameroomActions:
    def test_create_gameroom(self, db_session: Session):
        """게임룸 생성 액션 테스트"""
        # 게스트 생성
        guest_repo = GuestRepository(db_session)
        guest = guest_repo.create(uuid.uuid4(), "액션테스트")
        
        # 게임룸 액션 인스턴스
        actions = GameroomActions(db_session)
        
        # 게임룸 생성 데이터
        room_data = {
            "title": "액션 테스트 룸",
            "max_players": 6
        }
        
        # 게임룸 생성
        room, participant = actions.create_gameroom(room_data, guest.guest_id)
        
        # 검증
        assert room is not None
        assert room.title == "액션 테스트 룸"
        assert room.max_players == 6
        assert room.created_by == guest.guest_id
        assert room.participant_count == 1
        
        # 참가자 검증
        assert participant is not None
        assert participant.guest_id == guest.guest_id
        assert participant.is_creator is True
        
    def test_join_gameroom(self, db_session: Session):
        """게임룸 참가 액션 테스트"""
        # 게스트 생성
        guest_repo = GuestRepository(db_session)
        host = guest_repo.create(uuid.uuid4(), "방장")
        visitor = guest_repo.create(uuid.uuid4(), "참가자")
        
        # 게임룸 액션 인스턴스
        actions = GameroomActions(db_session)
        
        # 게임룸 생성
        room_data = {"title": "참가 테스트"}
        room, _ = actions.create_gameroom(room_data, host.guest_id)
        
        # 다른 사용자가 참가
        participant = actions.join_gameroom(room.room_id, visitor.guest_id)
        
        # 검증
        assert participant is not None
        assert participant.guest_id == visitor.guest_id
        assert participant.is_creator is False
        assert participant.status == ParticipantStatus.WAITING.value
        
        # 게임룸 참가자 수 증가 확인
        db_session.refresh(room)
        assert room.participant_count == 2
        
    def test_leave_gameroom(self, db_session: Session):
        """게임룸 퇴장 액션 테스트"""
        # 게스트 생성
        guest_repo = GuestRepository(db_session)
        host = guest_repo.create(uuid.uuid4(), "방장")
        visitor = guest_repo.create(uuid.uuid4(), "참가자")
        
        # 게임룸 액션 인스턴스
        actions = GameroomActions(db_session)
        
        # 게임룸 생성 및 참가
        room_data = {"title": "퇴장 테스트"}
        room, _ = actions.create_gameroom(room_data, host.guest_id)
        actions.join_gameroom(room.room_id, visitor.guest_id)
        
        # 참가자 퇴장
        result = actions.leave_gameroom(room.room_id, visitor.guest_id)
        
        # 검증
        assert result is True
        
        # 게임룸 참가자 수 감소 확인
        db_session.refresh(room)
        assert room.participant_count == 1
        
    def test_toggle_ready_status(self, db_session: Session):
        """준비 상태 전환 액션 테스트"""
        # 게스트 생성
        guest_repo = GuestRepository(db_session)
        host = guest_repo.create(uuid.uuid4(), "방장")
        visitor = guest_repo.create(uuid.uuid4(), "참가자")
        
        # 게임룸 액션 인스턴스
        actions = GameroomActions(db_session)
        
        # 게임룸 생성 및 참가
        room_data = {"title": "준비 테스트"}
        room, _ = actions.create_gameroom(room_data, host.guest_id)
        actions.join_gameroom(room.room_id, visitor.guest_id)
        
        # 참가자 준비 상태 전환
        new_status = actions.toggle_ready_status(room.room_id, visitor.guest_id)
        
        # 검증
        assert new_status == ParticipantStatus.READY.value
        
        # 다시 전환하면 WAITING 상태로 돌아가는지 확인
        new_status = actions.toggle_ready_status(room.room_id, visitor.guest_id)
        assert new_status == ParticipantStatus.WAITING.value
        
    def test_start_game(self, db_session: Session):
        """게임 시작 액션 테스트"""
        # 게스트 생성
        guest_repo = GuestRepository(db_session)
        host = guest_repo.create(uuid.uuid4(), "방장")
        visitor = guest_repo.create(uuid.uuid4(), "참가자")
        
        # 게임룸 액션 인스턴스
        actions = GameroomActions(db_session)
        
        # 게임룸 생성 및 참가
        room_data = {"title": "시작 테스트"}
        room, _ = actions.create_gameroom(room_data, host.guest_id)
        actions.join_gameroom(room.room_id, visitor.guest_id)
        
        # 참가자 준비 상태로 변경
        actions.toggle_ready_status(room.room_id, visitor.guest_id)
        
        # 게임 시작
        result = actions.start_game(room.room_id, host.guest_id)
        
        # 검증
        assert result is True
        
        # 게임 상태 확인
        db_session.refresh(room)
        assert room.status == GameStatus.PLAYING.value
        assert room.started_at is not None
        
        # 참가자 상태 확인
        host_participant = actions.gameroom_repo.find_participant(room.room_id, host.guest_id)
        visitor_participant = actions.gameroom_repo.find_participant(room.room_id, visitor.guest_id)
        
        assert host_participant.status == ParticipantStatus.PLAYING.value
        assert visitor_participant.status == ParticipantStatus.PLAYING.value 