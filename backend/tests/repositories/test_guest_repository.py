import uuid
from sqlalchemy.orm import Session

from repositories.guest_repository import GuestRepository


class TestGuestRepository:
    def test_create_guest(self, db_session: Session):
        """게스트 생성 테스트"""
        repo = GuestRepository(db_session)

        # 테스트 데이터
        test_uuid = uuid.uuid4()
        test_nickname = "테스트유저"
        test_device = "테스트기기"

        # 게스트 생성
        guest = repo.create(test_uuid, test_nickname, test_device)

        # 검증
        assert guest.guest_id is not None
        assert guest.uuid == test_uuid
        assert guest.nickname == test_nickname
        assert guest.device_info == test_device

    def test_find_by_uuid(self, db_session: Session):
        """UUID로 게스트 조회 테스트"""
        repo = GuestRepository(db_session)

        # 테스트 데이터 생성
        test_uuid = uuid.uuid4()
        test_nickname = "UUID조회테스트"

        # 게스트 생성
        created_guest = repo.create(test_uuid, test_nickname)

        # 조회 테스트
        found_guest = repo.find_by_uuid(test_uuid)

        # 검증
        assert found_guest is not None
        assert found_guest.guest_id == created_guest.guest_id
        assert found_guest.nickname == test_nickname

    def test_find_by_nickname(self, db_session: Session):
        """닉네임으로 게스트 조회 테스트"""
        repo = GuestRepository(db_session)

        # 테스트 데이터 생성
        test_uuid = uuid.uuid4()
        test_nickname = "닉네임조회테스트"

        # 게스트 생성
        repo.create(test_uuid, test_nickname)

        # 조회 테스트
        found_guest = repo.find_by_nickname(test_nickname)

        # 검증
        assert found_guest is not None
        assert found_guest.nickname == test_nickname

    def test_update_last_login(self, db_session: Session):
        """마지막 로그인 시간 업데이트 테스트"""
        repo = GuestRepository(db_session)

        # 테스트 데이터 생성
        test_uuid = uuid.uuid4()
        test_nickname = "로그인테스트"

        # 게스트 생성
        guest = repo.create(test_uuid, test_nickname)

        # 초기에는 last_login 없음
        assert guest.last_login is None

        # 시간 확인을 위해 잠시 대기
        import time

        time.sleep(0.1)

        # 로그인 시간 업데이트
        updated_guest = repo.update_last_login(guest, "새로운기기")

        # 검증
        assert updated_guest.last_login is not None
        assert updated_guest.device_info == "새로운기기"

    def test_update_nickname(self, db_session: Session):
        """닉네임 업데이트 테스트"""
        repo = GuestRepository(db_session)

        # 테스트 데이터 생성
        test_uuid = uuid.uuid4()
        old_nickname = "예전닉네임"
        new_nickname = "새닉네임"

        # 게스트 생성
        guest = repo.create(test_uuid, old_nickname)

        # 닉네임 업데이트
        updated_guest = repo.update_nickname(guest, new_nickname)

        # 검증
        assert updated_guest.nickname == new_nickname

        # DB에서 다시 조회해도 업데이트되어 있는지 확인
        found_guest = repo.find_by_uuid(test_uuid)
        assert found_guest.nickname == new_nickname
