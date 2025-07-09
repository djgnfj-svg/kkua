import pytest
import uuid
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request, HTTPException, status

from services.gameroom_service import GameroomService
from repositories.gameroom_repository import GameroomRepository
from repositories.guest_repository import GuestRepository
from services.game_state_service import GameStateService
from models.gameroom_model import (
    Gameroom,
    GameStatus,
    ParticipantStatus,
    GameroomParticipant,
)
from models.guest_model import Guest

# 모든 테스트에 asyncio 마커 추가
pytestmark = pytest.mark.asyncio


class TestGameroomService:
    def setup_method(self):
        """각 테스트 메소드 실행 전 설정"""
        self.mock_db = Mock()
        self.service = GameroomService(self.mock_db)
        self.service.repository = Mock(spec=GameroomRepository)
        self.service.guest_repository = Mock(spec=GuestRepository)
        self.service.game_state_service = Mock(spec=GameStateService)

        # ws_manager mock 설정
        self.service.ws_manager = Mock()
        self.service.ws_manager.broadcast_room_update = AsyncMock()

    def test_get_guest_by_cookie_success(self):
        """쿠키에서 게스트 UUID 추출 성공 테스트"""
        # 테스트 데이터 준비
        test_uuid = uuid.uuid4()

        # 요청 객체 mock 생성
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"kkua_guest_uuid": str(test_uuid)}

        # 게스트 객체 mock 생성
        mock_guest = Mock(spec=Guest)
        mock_guest.guest_id = 1
        mock_guest.nickname = "테스트유저"

        # 레포지토리 mock 반환값 설정
        self.guest_repository.find_by_uuid.return_value = mock_guest

        # 테스트 실행
        result = self.service.get_guest_by_cookie(mock_request)

        # 검증
        self.guest_repository.find_by_uuid.assert_called_once()
        assert result == mock_guest

    async def test_join_gameroom_success(self):
        """게임룸 참가 성공 테스트"""
        # 테스트 데이터 준비
        room_id = 1
        test_uuid = uuid.uuid4()

        # 요청 객체 mock 생성
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"kkua_guest_uuid": str(test_uuid)}

        # 게스트 객체 mock 생성
        mock_guest = Mock(spec=Guest)
        mock_guest.guest_id = 1
        mock_guest.nickname = "참가자"

        # 게임룸 객체 mock 생성
        mock_room = Mock(spec=Gameroom)
        mock_room.room_id = room_id
        mock_room.status = GameStatus.WAITING
        mock_room.max_players = 4

        # 참가자 객체 mock 생성
        mock_participant = Mock(spec=GameroomParticipant)
        mock_participant.participant_id = 1

        # 레포지토리 mock 반환값 설정
        self.guest_repository.find_by_uuid.return_value = mock_guest
        self.repository.find_by_id.return_value = mock_room
        self.repository.check_participation.return_value = None
        self.repository.find_active_participants.return_value = []
        self.repository.count_participants.return_value = 1
        self.repository.add_participant.return_value = mock_participant

        # 비동기 함수를 패치하여 동기 버전으로 대체
        with patch.object(self.service.ws_manager, "broadcast_room_update", return_value=None) as mock_broadcast:
            # 테스트 실행
            result = self.service.join_gameroom(room_id, mock_request)

            # 검증
            self.repository.find_by_id.assert_called_once()
            self.repository.check_participation.assert_called_once()
            self.repository.add_participant.assert_called_once()
            mock_broadcast.assert_called_once()
            assert result.room_id == room_id
            assert result.guest_id == mock_guest.guest_id
            assert "게임룸에 참가했습니다" in result.message

    def test_join_gameroom_room_not_found(self):
        """존재하지 않는 게임룸 참가 테스트"""
        # 테스트 데이터 준비
        room_id = 999
        test_uuid = uuid.uuid4()

        # 요청 객체 mock 생성
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"kkua_guest_uuid": str(test_uuid)}

        # 게스트 객체 mock 생성
        mock_guest = Mock(spec=Guest)
        mock_guest.guest_id = 1

        # 레포지토리 mock 반환값 설정
        self.guest_repository.find_by_uuid.return_value = mock_guest
        self.repository.find_by_id.return_value = None  # 게임룸이 존재하지 않음

        # 테스트 실행 및 예외 확인
        with pytest.raises(HTTPException) as excinfo:
            self.service.join_gameroom(room_id, mock_request)

        # 예외 검증
        assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
        assert "게임룸이 존재하지 않습니다" in excinfo.value.detail

    def test_join_gameroom_already_playing(self):
        """이미 시작된 게임 참가 테스트"""
        # 테스트 데이터 준비
        room_id = 1
        test_uuid = uuid.uuid4()

        # 요청 객체 mock 생성
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"kkua_guest_uuid": str(test_uuid)}

        # 게스트 객체 mock 생성
        mock_guest = Mock(spec=Guest)
        mock_guest.guest_id = 1

        # 게임룸 객체 mock 생성
        mock_room = Mock(spec=Gameroom)
        mock_room.room_id = room_id
        mock_room.status = GameStatus.PLAYING  # 이미 게임 중

        # 레포지토리 mock 반환값 설정
        self.guest_repository.find_by_uuid.return_value = mock_guest
        self.repository.find_by_id.return_value = mock_room

        # 테스트 실행 및 예외 확인
        with pytest.raises(HTTPException) as excinfo:
            self.service.join_gameroom(room_id, mock_request)

        # 예외 검증
        assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "게임이 이미 시작되었거나 종료된 방입니다" in excinfo.value.detail

    def test_join_gameroom_already_participating(self):
        """이미 참가 중인 게임룸 중복 참가 테스트"""
        # 테스트 데이터 준비
        room_id = 1
        test_uuid = uuid.uuid4()

        # 요청 객체 mock 생성
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"kkua_guest_uuid": str(test_uuid)}

        # 게스트 객체 mock 생성
        mock_guest = Mock(spec=Guest)
        mock_guest.guest_id = 1

        # 게임룸 객체 mock 생성
        mock_room = Mock(spec=Gameroom)
        mock_room.room_id = room_id
        mock_room.status = GameStatus.WAITING

        # 참가자 객체 mock 생성
        mock_participant = Mock(spec=GameroomParticipant)
        mock_participant.participant_id = 1

        # 레포지토리 mock 반환값 설정
        self.guest_repository.find_by_uuid.return_value = mock_guest
        self.repository.find_by_id.return_value = mock_room
        self.repository.check_participation.return_value = (
            mock_participant  # 이미 참가 중
        )

        # 테스트 실행 및 예외 확인
        with pytest.raises(HTTPException) as excinfo:
            self.service.join_gameroom(room_id, mock_request)

        # 예외 검증
        assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "이미 해당 게임룸에 참가 중입니다" in excinfo.value.detail

    async def test_leave_gameroom_success(self):
        """게임룸 나가기 성공 테스트"""
        # 테스트 데이터 준비
        room_id = 1
        test_uuid = uuid.uuid4()

        # 요청 객체 mock 생성
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"kkua_guest_uuid": str(test_uuid)}

        # 게스트 객체 mock 생성
        mock_guest = Mock(spec=Guest)
        mock_guest.guest_id = 2  # 방장이 아닌 ID
        mock_guest.nickname = "참가자"

        # 게임룸 객체 mock 생성
        mock_room = Mock(spec=Gameroom)
        mock_room.room_id = room_id
        mock_room.status = GameStatus.WAITING
        mock_room.created_by = 1  # 방장 ID (다른 ID)

        # 참가자 객체 mock 생성
        mock_participant = Mock(spec=GameroomParticipant)
        mock_participant.participant_id = 2
        mock_participant.guest_id = 2
        mock_participant.left_at = None

        # 레포지토리 mock 반환값 설정
        self.guest_repository.find_by_uuid.return_value = mock_guest
        self.repository.find_by_id.return_value = mock_room
        self.repository.find_participant.return_value = mock_participant
        self.repository.update_participant_left.return_value = True

        # 비동기 함수를 패치하여 동기 버전으로 대체
        with patch.object(self.service.ws_manager, "broadcast_room_update", return_value=None) as mock_broadcast:
            # 테스트 실행
            result = self.service.leave_gameroom(room_id, mock_request)

            # 검증
            self.repository.find_by_id.assert_called_once()
            self.repository.find_participant.assert_called_once()
            self.repository.update_participant_left.assert_called_once()
            mock_broadcast.assert_called_once()
            assert "게임룸에서 퇴장했습니다" in result["message"]

    async def test_leave_gameroom_as_creator(self):
        """방장이 게임룸 나가기 테스트 (방 삭제)"""
        # 테스트 데이터 준비
        room_id = 1
        test_uuid = uuid.uuid4()

        # 요청 객체 mock 생성
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"kkua_guest_uuid": str(test_uuid)}

        # 게스트 객체 mock 생성
        mock_guest = Mock(spec=Guest)
        mock_guest.guest_id = 1  # 방장 ID
        mock_guest.nickname = "방장"

        # 게임룸 객체 mock 생성
        mock_room = Mock(spec=Gameroom)
        mock_room.room_id = room_id
        mock_room.status = GameStatus.WAITING
        mock_room.created_by = 1  # 방장 ID (같은 ID)

        # 참가자 객체 mock 생성
        mock_participant = Mock(spec=GameroomParticipant)
        mock_participant.participant_id = 1
        mock_participant.guest_id = 1
        mock_participant.left_at = None

        # 다른 참가자 mock 생성
        mock_other_participant = Mock(spec=GameroomParticipant)
        mock_other_participant.participant_id = 2
        mock_other_participant.guest_id = 2
        mock_other_participant.left_at = None

        # 레포지토리 mock 반환값 설정
        self.guest_repository.find_by_uuid.return_value = mock_guest
        self.repository.find_by_id.return_value = mock_room
        self.repository.find_participant.return_value = mock_participant
        self.repository.update_participant_left.return_value = True
        self.repository.find_room_participants.return_value = [
            mock_participant,
            mock_other_participant,
        ]

        # DB mock 설정
        self.repository.db = Mock()
        self.repository.db.commit = Mock()

        # 비동기 함수를 패치하여 동기 버전으로 대체
        with patch.object(self.service.ws_manager, "broadcast_room_update", return_value=None) as mock_broadcast:
            # 테스트 실행
            result = self.service.leave_gameroom(room_id, mock_request)

            # 검증
            assert "방장이 퇴장하여 게임룸이 삭제되었습니다" in result["message"]
            self.repository.db.commit.assert_called_once()
            mock_broadcast.assert_called_once()

    async def test_start_game_success(self):
        """게임 시작 성공 테스트"""
        # 테스트 데이터 준비
        room_id = 1
        test_uuid = uuid.uuid4()

        # 요청 객체 mock 생성
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"kkua_guest_uuid": str(test_uuid)}

        # 게스트 객체 mock 생성
        mock_guest = Mock(spec=Guest)
        mock_guest.guest_id = 1  # 방장 ID

        # 게임룸 객체 mock 생성
        mock_room = Mock(spec=Gameroom)
        mock_room.room_id = room_id
        mock_room.status = GameStatus.WAITING
        mock_room.created_by = 1  # 방장 ID (같은 ID)

        # 레포지토리 mock 반환값 설정
        self.guest_repository.find_by_uuid.return_value = mock_guest
        self.repository.find_by_id.return_value = mock_room
        self.repository.count_participants.return_value = 2  # 최소 2명 참가
        self.repository.check_all_ready.return_value = True  # 모두 준비 완료
        self.repository.start_game.return_value = True

        # 비동기 함수를 패치하여 동기 버전으로 대체
        with patch.object(self.service.ws_manager, "broadcast_room_update", return_value=None) as mock_broadcast:
            # 테스트 실행
            result = self.service.start_game(room_id, mock_request)

            # 검증
            self.repository.start_game.assert_called_once()
            mock_broadcast.assert_called_once()
            assert "게임이 시작되었습니다" in result["message"]
            assert result["status"] == "PLAYING"

    async def test_toggle_ready_status(self):
        """준비 상태 토글 테스트"""
        # 테스트 데이터 준비
        room_id = 1
        test_uuid = uuid.uuid4()

        # 요청 객체 mock 생성
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"kkua_guest_uuid": str(test_uuid)}

        # 게스트 객체 mock 생성
        mock_guest = Mock(spec=Guest)
        mock_guest.guest_id = 2  # 방장이 아닌 ID
        mock_guest.nickname = "참가자"

        # 게임룸 객체 mock 생성
        mock_room = Mock(spec=Gameroom)
        mock_room.room_id = room_id
        mock_room.status = GameStatus.WAITING
        mock_room.created_by = 1  # 방장 ID (다른 ID)

        # 참가자 객체 mock 생성
        mock_participant = Mock(spec=GameroomParticipant)
        mock_participant.participant_id = 2
        mock_participant.status = ParticipantStatus.WAITING.value
        mock_participant.guest_id = 2
        mock_participant.room_id = room_id
        mock_participant.left_at = None

        # 레포지토리 mock 반환값 설정
        self.guest_repository.find_by_uuid.return_value = mock_guest
        self.repository.find_by_id.return_value = mock_room
        self.repository.find_participant.return_value = mock_participant
        self.repository.update_participant_status.return_value = True

        # 비동기 함수를 패치하여 동기 버전으로 대체
        with patch.object(self.service.ws_manager, "broadcast_room_update", return_value=None) as mock_broadcast:
            # 테스트 실행
            result = self.service.toggle_ready_status(room_id, mock_request)

            # 검증
            self.repository.update_participant_status.assert_called_once()
            mock_broadcast.assert_called_once()
            assert "준비 완료" in result["message"]
            assert result["is_ready"] is True

    def test_check_active_game(self):
        """활성 게임 확인 테스트"""
        # 테스트 데이터 준비
        test_uuid = uuid.uuid4()
        active_room_id = 1

        # 요청 객체 mock 생성
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"kkua_guest_uuid": str(test_uuid)}

        # 게스트 객체 mock 생성
        mock_guest = Mock(spec=Guest)
        mock_guest.guest_id = 1

        # 레포지토리 mock 반환값 설정
        self.guest_repository.find_by_uuid.return_value = mock_guest
        self.guest_repository.check_active_game.return_value = (True, active_room_id)

        # 테스트 실행
        result = self.service.check_active_game(mock_request)

        # 검증
        assert result["has_active_game"] is True
        assert result["room_id"] == active_room_id
