from repositories.guest_repository import GuestRepository
from schemas.guest_schema import GuestResponse
from fastapi import Response, HTTPException, status
import uuid
from typing import Optional

class GuestService:
    def __init__(self, repository: GuestRepository):
        self.repository = repository
    
    def login(self, response: Response, guest_uuid: Optional[str] = None, nickname: Optional[str] = None, device_info: Optional[str] = None) -> GuestResponse:
        """게스트 로그인 또는 새 게스트 생성을 처리합니다."""
        
        # UUID가 제공된 경우 해당 게스트 검색
        if guest_uuid:
            try:
                # UUID 객체로 변환
                if isinstance(guest_uuid, str):
                    if len(guest_uuid) == 32 and '-' not in guest_uuid:
                        guest_uuid = f"{guest_uuid[:8]}-{guest_uuid[8:12]}-{guest_uuid[12:16]}-{guest_uuid[16:20]}-{guest_uuid[20:]}"
                    
                    uuid_obj = uuid.UUID(str(guest_uuid))
                else:
                    uuid_obj = guest_uuid
                
                # 변환된 UUID로 게스트 검색
                guest = self.repository.find_by_uuid(uuid_obj)
                if not guest:
                    # 존재하지 않는 UUID인 경우 해당 UUID로 새 게스트 생성
                    nickname = f"Guest_{str(uuid_obj)[:8]}"
                    guest = self.repository.create(uuid_obj, nickname, device_info)
                    
                # 마지막 로그인 시간 업데이트
                guest = self.repository.update_last_login(guest, device_info)
                
            except ValueError:
                # UUID 형식이 잘못된 경우
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="유효하지 않은 UUID 형식입니다."
                )
            except Exception as e:
                # 기타 오류
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"게스트 로그인 처리 중 오류가 발생했습니다: {str(e)}"
                )
        else:
            # UUID가 제공되지 않은 경우 새 게스트 생성
            new_uuid = uuid.uuid4()
            nickname = f"Guest_{str(new_uuid)[:8]}"
            guest = self.repository.create(new_uuid, nickname, device_info)

        # 쿠키 설정
        self._set_auth_cookies(response, guest.uuid)

        # 게임 중인지 확인하고 리다이렉션 정보 추가
        should_redirect, room_id = self.repository.check_active_game(guest.guest_id)

        # 응답 생성
        result = GuestResponse.model_validate(guest)
        if should_redirect:
            result.active_game = {"room_id": room_id}
        return result

    def _set_auth_cookies(self, response: Response, uuid_value: uuid.UUID):
        """인증 쿠키를 설정합니다."""
        uuid_str = str(uuid_value)
        cookie_options = {
            "max_age": 3600 * 24 * 30,
            "secure": False,  # 프로덕션에서는 True로
            "samesite": "lax"
        }
        
        # 1. 보안 인증용 HttpOnly 쿠키 (서버에서만 접근 가능)
        response.set_cookie(
            key="kkua_guest_auth", 
            value=uuid_str,
            httponly=True,
            **cookie_options
        )

        # 2. 프론트엔드 식별용 쿠키 (JavaScript에서 접근 가능)
        response.set_cookie(
            key="kkua_guest_uuid", 
            value=uuid_str,
            httponly=False,
            **cookie_options
        ) 