from sqlalchemy.orm import Session
from models.guest_model import Guest
from models.gameroom_model import GameroomParticipant
import uuid
import datetime
from typing import Optional


class GuestRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_uuid(self, guest_uuid: uuid.UUID) -> Optional[Guest]:
        try:
            guest = self.db.query(Guest).filter(Guest.uuid == guest_uuid).first()
            return guest
        except Exception as e:
            import logging

            logging.error(f"게스트 검색 중 오류 발생: {str(e)}")
            return None

    def find_by_nickname(self, nickname: str) -> Guest:
        return self.db.query(Guest).filter(Guest.nickname == nickname).first()

    def create(
        self, uuid_obj: uuid.UUID, nickname: str, device_info: Optional[str] = None
    ) -> Guest:
        guest = Guest(uuid=uuid_obj, nickname=nickname, device_info=device_info)
        self.db.add(guest)
        self.db.commit()
        self.db.refresh(guest)
        return guest

    def update_last_login(
        self, guest: Guest, device_info: Optional[str] = None
    ) -> Guest:
        """마지막 로그인 시간을 업데이트합니다."""
        guest.last_login = datetime.datetime.utcnow()
        if device_info:
            guest.device_info = device_info
        self.db.commit()
        self.db.refresh(guest)
        return guest

    def update_nickname(self, guest: Guest, new_nickname: str) -> Guest:
        """게스트의 닉네임을 업데이트합니다."""
        guest.nickname = new_nickname
        self.db.commit()
        self.db.refresh(guest)
        return guest

    def check_active_game(self, guest_id: int) -> tuple[bool, int]:
        """게스트가 현재 참여 중인 게임이 있는지 확인합니다."""
        return GameroomParticipant.should_redirect_to_game(self.db, guest_id)
