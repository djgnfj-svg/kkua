import pytest
import uuid
from unittest.mock import Mock
from fastapi import Request, HTTPException, status

from services.gameroom_service import GameroomService
from repositories.gameroom_repository import GameroomRepository
from repositories.guest_repository import GuestRepository
from repositories.gameroom_actions import GameroomActions
from models.gameroom_model import Gameroom, GameStatus, GameroomParticipant
from models.guest_model import Guest


class TestGameroomService:
    def setup_method(self):
        """각 테스트 메소드 실행 전 설정"""
        self.mock_db = Mock()
        self.service = GameroomService(self.mock_db)
        self.service.repository = Mock(spec=GameroomRepository)
        self.service.actions = Mock(spec=GameroomActions)
        self.service.guest_repository = Mock(spec=GuestRepository)

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
        self.service.guest_repository.find_by_uuid.return_value = mock_guest

        # 테스트 실행
        result = self.service.get_guest_by_cookie(mock_request)

        # 검증
        self.service.guest_repository.find_by_uuid.assert_called_once()
        assert result == mock_guest

    def test_get_guest_by_cookie_missing_cookie(self):
        """쿠키가 없는 경우 테스트"""
        # 요청 객체 mock 생성 (쿠키 없음)
        mock_request = Mock(spec=Request)
        mock_request.cookies = {}

        # 테스트 실행 및 예외 확인
        with pytest.raises(HTTPException) as excinfo:
            self.service.get_guest_by_cookie(mock_request)

        # 예외 검증
        assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "게스트 UUID가 필요합니다" in excinfo.value.detail

    def test_get_guest_by_cookie_invalid_uuid(self):
        """유효하지 않은 UUID 형식 테스트"""
        # 요청 객체 mock 생성 (잘못된 UUID)
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"kkua_guest_uuid": "invalid-uuid"}

        # 테스트 실행 및 예외 확인
        with pytest.raises(HTTPException) as excinfo:
            self.service.get_guest_by_cookie(mock_request)

        # 예외 검증
        assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "유효하지 않은 UUID 형식입니다" in excinfo.value.detail

    def test_get_guest_by_cookie_guest_not_found(self):
        """존재하지 않는 게스트 UUID 테스트"""
        # 테스트 데이터 준비
        test_uuid = uuid.uuid4()

        # 요청 객체 mock 생성
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"kkua_guest_uuid": str(test_uuid)}

        # 레포지토리 mock 반환값 설정
        self.service.guest_repository.find_by_uuid.return_value = None

        # 테스트 실행 및 예외 확인
        with pytest.raises(HTTPException) as excinfo:
            self.service.get_guest_by_cookie(mock_request)

        # 예외 검증
        assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
        assert "유효하지 않은 게스트 UUID입니다" in excinfo.value.detail

    def test_list_gamerooms(self):
        """게임룸 목록 조회 테스트"""
        # mock 게임룸 목록 생성
        mock_gamerooms = [Mock(spec=Gameroom) for _ in range(3)]

        # 필터 설정
        status_filter = GameStatus.WAITING

        # 레포지토리 mock 반환값 설정
        self.service.repository.find_all.return_value = mock_gamerooms

        # 테스트 실행
        result = self.service.list_gamerooms(status=status_filter)

        # 검증
        self.service.repository.find_all.assert_called_once()
        assert result == mock_gamerooms

    def test_get_gameroom(self):
        """게임룸 상세 조회 테스트"""
        # 테스트 데이터
        room_id = 1

        # mock 게임룸 생성
        mock_room = Mock(spec=Gameroom)
        mock_room.room_id = room_id

        # 레포지토리 mock 반환값 설정
        self.service.repository.find_by_id.return_value = mock_room

        # 테스트 실행
        result = self.service.get_gameroom(room_id)

        # 검증
        self.service.repository.find_by_id.assert_called_once_with(room_id)
        assert result == mock_room

    def test_create_gameroom(self):
        """게임룸 생성 테스트"""
        # 테스트 데이터 준비
        test_data = {
            "title": "테스트 게임룸",
            "max_players": 4,
            "description": "테스트 설명",
        }
        test_guest_id = 1

        # mock 게임룸 생성
        mock_room = Mock(spec=Gameroom)
        mock_room.room_id = 1
        mock_room.title = test_data["title"]
        mock_room.status = GameStatus.WAITING

        # 액션 mock 반환값 설정
        self.service.actions.create_gameroom.return_value = (mock_room, None)

        # 테스트 실행
        result = self.service.create_gameroom(test_data, test_guest_id)

        # 검증
        self.service.actions.create_gameroom.assert_called_once_with(
            test_data, test_guest_id
        )
        assert result == mock_room

    def test_update_gameroom(self):
        """게임룸 정보 업데이트 테스트"""
        # 테스트 데이터 준비
        room_id = 1
        update_data = {"title": "업데이트된 제목", "description": "업데이트된 설명"}

        # mock 게임룸 생성
        mock_room = Mock(spec=Gameroom)
        mock_room.room_id = room_id
        mock_room.title = update_data["title"]

        # 레포지토리 mock 반환값 설정
        self.service.repository.update.return_value = mock_room

        # 테스트 실행
        result = self.service.update_gameroom(room_id, update_data)

        # 검증
        self.service.repository.update.assert_called_once_with(room_id, update_data)
        assert result == mock_room

    def test_delete_gameroom(self):
        """게임룸 삭제 테스트"""
        # 테스트 데이터
        room_id = 1

        # 레포지토리 mock 반환값 설정
        self.service.repository.delete.return_value = True

        # 테스트 실행
        result = self.service.delete_gameroom(room_id)

        # 검증
        self.service.repository.delete.assert_called_once_with(room_id)
        assert result is True

    def test_join_gameroom(self):
        """게임룸 참가 테스트"""
        # 테스트 데이터
        room_id = 1
        guest_id = 1

        # mock 참가자 객체 생성
        mock_participant = Mock(spec=GameroomParticipant)
        mock_participant.participant_id = 1
        mock_participant.room_id = room_id
        mock_participant.guest_id = guest_id

        # 액션 mock 반환값 설정
        self.service.actions.join_gameroom.return_value = mock_participant

        # 테스트 실행
        result = self.service.join_gameroom(room_id, guest_id)

        # 검증
        self.service.actions.join_gameroom.assert_called_once_with(room_id, guest_id)
        assert result == mock_participant

    def test_leave_gameroom(self):
        """게임룸 나가기 테스트"""
        # 테스트 데이터
        room_id = 1
        guest_id = 1

        # 액션 mock 반환값 설정
        self.service.actions.leave_gameroom.return_value = True

        # 테스트 실행
        result = self.service.leave_gameroom(room_id, guest_id)

        # 검증
        self.service.actions.leave_gameroom.assert_called_once_with(room_id, guest_id)
        assert result is True

    def test_toggle_ready_status(self):
        """준비 상태 토글 테스트"""
        # 테스트 데이터
        room_id = 1
        guest_id = 1
        new_status = "READY"

        # 액션 mock 반환값 설정
        self.service.actions.toggle_ready_status.return_value = new_status

        # 테스트 실행
        result = self.service.toggle_ready_status(room_id, guest_id)

        # 검증
        self.service.actions.toggle_ready_status.assert_called_once_with(
            room_id, guest_id
        )
        assert result == new_status

    def test_start_game(self):
        """게임 시작 테스트"""
        # 테스트 데이터
        room_id = 1
        host_id = 1

        # 액션 mock 반환값 설정
        self.service.actions.start_game.return_value = True

        # 테스트 실행
        result = self.service.start_game(room_id, host_id)

        # 검증
        self.service.actions.start_game.assert_called_once_with(room_id, host_id)
        assert result is True

    def test_end_game(self):
        """게임 종료 테스트"""
        # 테스트 데이터
        room_id = 1

        # 액션 mock 반환값 설정
        self.service.actions.end_game.return_value = True

        # 테스트 실행
        result = self.service.end_game(room_id)

        # 검증
        self.service.actions.end_game.assert_called_once_with(room_id)
        assert result is True

    def test_get_participants(self):
        """게임룸 참가자 목록 조회 테스트"""
        # 테스트 데이터
        room_id = 1

        # mock 참가자 목록 생성
        mock_participants = [
            {"guest_id": 1, "nickname": "참가자1", "status": "READY"},
            {"guest_id": 2, "nickname": "참가자2", "status": "WAITING"},
        ]

        # 레포지토리 mock 반환값 설정
        self.service.repository.get_participants.return_value = mock_participants

        # 테스트 실행
        result = self.service.get_participants(room_id)

        # 검증
        self.service.repository.get_participants.assert_called_once_with(room_id)
        assert result == mock_participants
