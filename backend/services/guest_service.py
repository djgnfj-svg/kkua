from repositories.guest_repository import GuestRepository
from schemas.guest_schema import GuestResponse
from fastapi import Response
import uuid
from typing import Optional

class GuestService:
    def __init__(self, repository: GuestRepository):
        self.repository = repository
    
    def login(self, response: Response, guest_uuid: Optional[str] = None, nickname: Optional[str] = None, device_info: Optional[str] = None) -> GuestResponse:
        """게스트 로그인 또는 새 게스트 생성을 처리합니다."""
        guest = None
        
        # UUID로 로그인 시도
        if guest_uuid:
            try:
                uuid_obj = uuid.UUID(guest_uuid)
                guest = self.repository.find_by_uuid(uuid_obj)
            except (ValueError, TypeError):
                pass
        
        if not guest:
            # 게스트 생성
            new_uuid = uuid.uuid4()
            # 고유한 닉네임 생성 및 검증
            if nickname:
                # 사용자가 제공한 닉네임이 있으면 중복 확인
                existing = self.repository.find_by_nickname(nickname)
                if existing:
                    # 중복된 닉네임이면 새로 생성
                    nickname = f"Guest_{str(new_uuid)[:8]}"
            else:
                # 닉네임이 없으면 UUID로 생성
                nickname = f"Guest_{str(new_uuid)[:8]}"
                
            # 닉네임 중복 확인 및 생성
            while True:
                existing = self.repository.find_by_nickname(nickname)
                if not existing:
                    break
                # 중복이면 다른 닉네임 생성
                nickname = f"Guest_{str(uuid.uuid4())[:8]}"
            
            guest = self.repository.create(new_uuid, nickname, device_info)
        else:
            # 마지막 로그인 시간 업데이트 및 디바이스 정보 갱신
            guest = self.repository.update_last_login(guest, device_info)
        
        # 게스트 UUID 쿠키 설정
        response.set_cookie(
            key="kkua_guest_uuid", 
            value=str(guest.uuid),
            httponly=True,
            max_age=3600 * 24 * 30,  # 30일
            secure=False,  # 프로덕션에서는 True로 설정
            samesite="lax"
        )
        
        # 게임 중인지 확인하고 리다이렉션 정보 추가
        should_redirect, room_id = self.repository.check_active_game(guest.guest_id)
        
        result = GuestResponse.model_validate(guest)
        if should_redirect:
            result.active_game = {"room_id": room_id}
        
        return result 