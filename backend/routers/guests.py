from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.orm import Session
from typing import Optional
from models.guest import Guest
from schemas.guest import GuestResponse
from db.postgres import get_db
import uuid
import datetime
from models.gameroom_participant import GameroomParticipant

router = APIRouter(
    prefix="/guests",
    tags=["guests"],
)

@router.post("/login", response_model=GuestResponse)
def guest_login(request: Request, response: Response, db: Session = Depends(get_db), guest_uuid: Optional[str] = None):
    guest = None
    
    # 파라미터로 전달된 UUID 또는 쿠키에서 UUID 확인
    if not guest_uuid:
        guest_uuid = request.cookies.get("kkua_guest_uuid")

    # UUID로 로그인 시도
    if guest_uuid:
        try:
            uuid_obj = uuid.UUID(guest_uuid)
            guest = db.query(Guest).filter(Guest.uuid == uuid_obj).first()
        except (ValueError, TypeError):
            pass

    if not guest:
        # 게스트 생성
        new_uuid = uuid.uuid4()
        # 고유한 닉네임 생성 및 검증
        while True:
            nickname = f"Guest_{str(new_uuid)[:8]}"
            existing = db.query(Guest).filter(Guest.nickname == nickname).first()
            if not existing:
                break
        
        guest = Guest(uuid=new_uuid, nickname=nickname)
        db.add(guest)
        db.commit()
        db.refresh(guest)
    else:
        # 마지막 로그인 시간 업데이트
        guest.last_login = datetime.datetime.utcnow()
        db.commit()
        db.refresh(guest)

    # 게스트 UUID 쿠키 설정 (새로 생성된 게스트 포함)
    response.set_cookie(
        key="kkua_guest_uuid", 
        value=str(guest.uuid),
        httponly=True,
        max_age=3600 * 24 * 30,  # 30일
        secure=False,  # 프로덕션에서는 True로 설정
        samesite="lax"
    )
    
    # 게임 중인지 확인하고 리다이렉션 정보 추가
    should_redirect, room_id = GameroomParticipant.should_redirect_to_game(db, guest.guest_id)
    
    result = GuestResponse.model_validate(guest)
    if should_redirect:
        result.active_game = {"room_id": room_id}
    
    return result
