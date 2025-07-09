import pytest
import uuid
from unittest.mock import Mock, patch
from fastapi import Response, HTTPException, status
from datetime import datetime

from services.guest_service import GuestService
from repositories.guest_repository import GuestRepository
from models.guest_model import Guest


class TestGuestService:
    def setup_method(self):
        """각 테스트 메소드 실행 전 설정"""
        self.repository = Mock(spec=GuestRepository)
        self.service = GuestService(self.repository)
        self.mock_response = Mock(spec=Response)
        self.mock_response.set_cookie = Mock()

    def test_login_with_valid_uuid(self):
        """유효한 UUID로 로그인 테스트"""
        # 테스트 데이터 준비
        test_uuid = uuid.uuid4()
        test_nickname = "테스트유저"

        # 실제 Guest 객체 생성 (Mock이 아닌)
        guest = Guest(
            guest_id=1,
            uuid=test_uuid,
            nickname=test_nickname,
            created_at=datetime.now(),
            last_login=datetime.now(),
            device_info="테스트 디바이스",
        )

        # 레포지토리 mock 반환값 설정 - 실제 Guest 객체 사용
        self.repository.find_by_uuid.return_value = guest
        self.repository.update_last_login.return_value = guest
        self.repository.check_active_game.return_value = (False, None)

        # 테스트 실행
        result = self.service.login(
            response=self.mock_response,
            guest_uuid=str(test_uuid),
            nickname=test_nickname,
            device_info="테스트 디바이스",
        )

        # 검증
        self.repository.find_by_uuid.assert_called_once()
        self.repository.update_last_login.assert_called_once()
        self.mock_response.set_cookie.assert_called()
        assert result.nickname == test_nickname

    def test_login_with_nonexistent_uuid(self):
        """존재하지 않는 UUID로 로그인 테스트 (새 게스트 생성)"""
        # 테스트 데이터 준비
        test_uuid = uuid.uuid4()
        test_nickname = "새로운유저"

        # 실제 Guest 객체 생성
        guest = Guest(
            guest_id=2,
            uuid=test_uuid,
            nickname=test_nickname,
            created_at=datetime.now(),
            last_login=datetime.now(),
            device_info="테스트 디바이스",
        )

        # 레포지토리 mock 반환값 설정
        self.repository.find_by_uuid.return_value = None  # UUID가 존재하지 않음
        self.repository.create.return_value = guest
        self.repository.update_last_login.return_value = guest
        self.repository.check_active_game.return_value = (False, None)

        # 테스트 실행
        result = self.service.login(
            response=self.mock_response,
            guest_uuid=str(test_uuid),
            nickname=test_nickname,
            device_info="테스트 디바이스",
        )

        # 검증
        self.repository.find_by_uuid.assert_called_once()
        self.repository.create.assert_called_once()
        self.mock_response.set_cookie.assert_called()
        assert result.nickname == test_nickname

    def test_login_with_invalid_uuid(self):
        """유효하지 않은 형식의 UUID 테스트"""
        # 유효하지 않은 UUID로 로그인 시도
        with pytest.raises(HTTPException) as excinfo:
            self.service.login(
                response=self.mock_response,
                guest_uuid="invalid-uuid-format",
                device_info="테스트 디바이스",
            )

        # 오류 코드 및 메시지 검증
        assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "유효하지 않은 UUID 형식입니다" in excinfo.value.detail

    def test_login_new_guest(self):
        """새 게스트 생성 테스트 (UUID 없이 호출)"""
        # 테스트 데이터 준비
        test_nickname = "새 게스트"
        test_uuid = uuid.uuid4()  # 서비스에서 생성될 UUID 대신 사용

        # 실제 Guest 객체 생성
        guest = Guest(
            guest_id=3,
            uuid=test_uuid,
            nickname=test_nickname,
            created_at=datetime.now(),
            last_login=datetime.now(),
            device_info="테스트 디바이스",
        )

        # 레포지토리 mock 반환값 설정
        self.repository.create.return_value = guest
        self.repository.check_active_game.return_value = (False, None)

        # UUID 생성 함수 패치
        with patch("uuid.uuid4", return_value=test_uuid):
            # 테스트 실행 (UUID 없이 호출)
            result = self.service.login(
                response=self.mock_response,
                guest_uuid=None,
                nickname=test_nickname,
                device_info="테스트 디바이스",
            )

        # 검증
        self.repository.create.assert_called_once()
        self.mock_response.set_cookie.assert_called()
        assert result.nickname == test_nickname

    def test_login_with_active_game(self):
        """활성 게임이 있는 게스트 로그인 테스트"""
        # 테스트 데이터 준비
        test_uuid = uuid.uuid4()
        test_room_id = 123
        test_nickname = "게임중인유저"

        # 실제 Guest 객체 생성
        guest = Guest(
            guest_id=4,
            uuid=test_uuid,
            nickname=test_nickname,
            created_at=datetime.now(),
            last_login=datetime.now(),
            device_info="테스트 디바이스",
        )

        # 레포지토리 mock 반환값 설정
        self.repository.find_by_uuid.return_value = guest
        self.repository.update_last_login.return_value = guest
        self.repository.check_active_game.return_value = (True, test_room_id)

        # 테스트 실행
        result = self.service.login(
            response=self.mock_response,
            guest_uuid=str(test_uuid),
            device_info="테스트 디바이스",
        )

        # 검증
        self.repository.check_active_game.assert_called_once_with(guest.guest_id)
        assert result.active_game is not None
        assert result.active_game["room_id"] == test_room_id

    def test_parse_uuid(self):
        """UUID 파싱 테스트"""
        # 일반 형식의 UUID
        normal_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = self.service._parse_uuid(normal_uuid)
        assert isinstance(result, uuid.UUID)
        assert str(result) == normal_uuid

        # 하이픈 없는 UUID
        uuid_without_hyphens = "550e8400e29b41d4a716446655440000"
        result = self.service._parse_uuid(uuid_without_hyphens)
        assert isinstance(result, uuid.UUID)
        assert str(result).replace("-", "") == uuid_without_hyphens

    def test_set_auth_cookies(self):
        """인증 쿠키 설정 테스트"""
        test_uuid = uuid.uuid4()

        # 쿠키 설정 호출
        self.service._set_auth_cookies(self.mock_response, test_uuid)

        # 검증 - 두 종류의 쿠키가 설정되어야 함
        assert self.mock_response.set_cookie.call_count == 2
