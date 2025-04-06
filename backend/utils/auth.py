from fastapi import Depends, Cookie, HTTPException, status
from sqlalchemy.orm import Session
from db.postgres import get_db
from models.guest import Guest
from typing import Optional
import datetime
import uuid

def get_current_guest(
    guest_uuid: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    if not guest_uuid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증되지 않은 요청",
        )
    
    try:
        uuid_obj = uuid.UUID(guest_uuid)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보",
        )
    
    guest = db.query(Guest).filter(Guest.uuid == uuid_obj).first()
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="게스트를 찾을 수 없습니다",
        )
    
    # 접속 시 마지막 로그인 시간 업데이트
    guest.last_login = datetime.datetime.utcnow()
    db.commit()
    
    return guest 