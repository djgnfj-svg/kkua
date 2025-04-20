from sqlalchemy.orm import Session
from sqlalchemy import text
from models.guest_model import Guest
from models.gameroom_model import GameroomParticipant
import uuid
import datetime
from typing import Optional
from sqlalchemy import String

class GuestRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_uuid(self, guest_uuid: uuid.UUID) -> Optional[Guest]:
        """UUID로 게스트를 찾습니다."""
        print(f"게스트 UUID 조회 시도: {guest_uuid}, 타입: {type(guest_uuid).__name__}")
        
        try:
            # UUID 문자열로 변환
            uuid_str = str(guest_uuid)
            
            # 1. 일반적인 ORM 쿼리 시도
            guest = self.db.query(Guest).filter(Guest.uuid == guest_uuid).first()
            if guest:
                print(f"ORM으로 게스트 찾음: {guest.guest_id}")
                return guest
            
            # 2. 문자열 비교 ORM 쿼리 시도
            from sqlalchemy import cast, String
            guest = self.db.query(Guest).filter(cast(Guest.uuid, String) == uuid_str).first()
            if guest:
                print(f"문자열 변환 ORM으로 게스트 찾음: {guest.guest_id}")
                return guest
            
            # 3. 더 다양한 SQL 쿼리 시도
            # PostgreSQL의 UUID에 대한 다양한 형식 시도
            sql = text("""
                SELECT * FROM guests 
                WHERE uuid::text = :uuid 
                   OR uuid = :uuid_raw 
                   OR LOWER(uuid::text) = LOWER(:uuid)
                   OR REPLACE(uuid::text, '-', '') = REPLACE(:uuid, '-', '')
            """)
            result = self.db.execute(sql, {"uuid": uuid_str, "uuid_raw": guest_uuid})
            row = result.first()
            
            if row:
                print(f"SQL 쿼리로 게스트 찾음: {row.guest_id}")
                return Guest(
                    guest_id=row.guest_id,
                    uuid=uuid.UUID(row.uuid) if isinstance(row.uuid, str) else row.uuid,
                    nickname=row.nickname,
                    created_at=row.created_at,
                    last_login=row.last_login,
                    device_info=row.device_info
                )
            
            print(f"모든 방법으로 게스트를 찾을 수 없음: {uuid_str}")
            return None
        except Exception as e:
            print(f"게스트 검색 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def find_by_nickname(self, nickname: str) -> Guest:
        return self.db.query(Guest).filter(Guest.nickname == nickname).first()
    
    def create(self, uuid_obj: uuid.UUID, nickname: str, device_info: Optional[str] = None) -> Guest:
        """새 게스트를 생성합니다."""
        guest = Guest(uuid=uuid_obj, nickname=nickname, device_info=device_info)
        self.db.add(guest)
        self.db.commit()
        self.db.refresh(guest)
        return guest
    
    def update_last_login(self, guest: Guest, device_info: Optional[str] = None) -> Guest:
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