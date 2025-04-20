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
        
        print(f"----로그인 요청 받음----")
        print(f"입력 UUID: {guest_uuid}, 타입: {type(guest_uuid).__name__ if guest_uuid else 'None'}")
        print(f"입력 닉네임: {nickname}")
        
        # UUID로 로그인 시도
        if guest_uuid:
            try:
                # UUID 객체로 변환 (문자열이든 아니든)
                if isinstance(guest_uuid, str):
                    # 문자열에서 하이픈(-) 이 없는 경우 추가
                    if len(guest_uuid) == 32 and '-' not in guest_uuid:
                        guest_uuid = f"{guest_uuid[:8]}-{guest_uuid[8:12]}-{guest_uuid[12:16]}-{guest_uuid[16:20]}-{guest_uuid[20:]}"
                    
                    uuid_obj = uuid.UUID(str(guest_uuid))
                else:
                    uuid_obj = guest_uuid
                
                print(f"변환된 UUID: {uuid_obj}, 타입: {type(uuid_obj).__name__}")
                
                # 변환된 UUID로 게스트 검색
                guest = self.repository.find_by_uuid(uuid_obj)
                
                if guest:
                    print(f"기존 게스트 찾음: guest_id={guest.guest_id}, nickname={guest.nickname}")
                    
                    # 닉네임 업데이트가 필요한 경우
                    if nickname and nickname != guest.nickname:
                        guest = self.repository.update_nickname(guest, nickname)
                        print(f"닉네임 업데이트: {guest.nickname}")
                    
                    # 마지막 로그인 시간 업데이트
                    guest = self.repository.update_last_login(guest, device_info)
                    print(f"로그인 시간 업데이트됨")
                    
                    # 1. 보안 인증용 HttpOnly 쿠키 (서버에서만 접근 가능)
                    response.set_cookie(
                        key="kkua_guest_auth", 
                        value=str(guest.uuid),
                        httponly=True,       # JavaScript에서 접근 불가
                        max_age=3600 * 24 * 30,
                        secure=False,        # 프로덕션에서는 True로
                        samesite="lax"
                    )
                    
                    # 2. 프론트엔드 식별용 쿠키 (JavaScript에서 접근 가능)
                    response.set_cookie(
                        key="kkua_guest_uuid", 
                        value=str(guest.uuid),
                        httponly=False,      # JavaScript에서 접근 가능
                        max_age=3600 * 24 * 30,
                        secure=False,        # 프로덕션에서는 True로
                        samesite="lax"
                    )
                    
                    # 게임 중인지 확인하고 리다이렉션 정보 추가
                    should_redirect, room_id = self.repository.check_active_game(guest.guest_id)
                    
                    result = GuestResponse.model_validate(guest)
                    if should_redirect:
                        result.active_game = {"room_id": room_id}
                    
                    return result
                    
            except ValueError as e:
                print(f"UUID 변환 오류: {str(e)}")
                guest = None
            except Exception as e:
                print(f"게스트 검색 오류: {str(e)}")
                guest = None
        
        # 여기까지 왔다면 게스트를 찾지 못했거나 UUID가 유효하지 않음
        print("게스트를 찾지 못했거나 UUID가 유효하지 않음, 새 게스트 생성")
        
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
        print(f"새 게스트 생성: guest_id={guest.guest_id}, nickname={guest.nickname}, uuid={guest.uuid}")
        
        # 1. 보안 인증용 HttpOnly 쿠키 (서버에서만 접근 가능)
        response.set_cookie(
            key="kkua_guest_auth", 
            value=str(guest.uuid),
            httponly=True,       # JavaScript에서 접근 불가
            max_age=3600 * 24 * 30,
            secure=False,        # 프로덕션에서는 True로
            samesite="lax"
        )
        
        # 2. 프론트엔드 식별용 쿠키 (JavaScript에서 접근 가능)
        response.set_cookie(
            key="kkua_guest_uuid", 
            value=str(guest.uuid),
            httponly=False,      # JavaScript에서 접근 가능
            max_age=3600 * 24 * 30,
            secure=False,        # 프로덕션에서는 True로
            samesite="lax"
        )
        
        # 게임 중인지 확인하고 리다이렉션 정보 추가
        should_redirect, room_id = self.repository.check_active_game(guest.guest_id)
        
        result = GuestResponse.model_validate(guest)
        if should_redirect:
            result.active_game = {"room_id": room_id}
        
        return result 