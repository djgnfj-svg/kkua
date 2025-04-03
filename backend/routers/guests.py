from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie
from sqlalchemy.orm import Session
from typing import List, Optional
from models.guest import Guest
from schemas.guest import GuestCreate, GuestResponse, GuestUpdate
from db.postgres import get_db
import uuid
import datetime

router = APIRouter(
    prefix="/guests",
    tags=["guests"],
)

@router.post("/", response_model=GuestResponse, status_code=status.HTTP_201_CREATED)
def create_guest(guest: GuestCreate, response: Response, db: Session = Depends(get_db)):
    # 닉네임이 없는 경우 기본값 설정 또는 그냥 None으로 둘 수 있습니다
    db_guest = Guest(nickname=guest.nickname, last_login=datetime.datetime.utcnow())
    db.add(db_guest)
    db.commit()
    db.refresh(db_guest)
    
    # 쿠키에 게스트 UUID 저장
    response.set_cookie(
        key="guest_uuid", 
        value=str(db_guest.uuid),
        httponly=True,
        max_age=3600 * 24 * 30,  # 30일
        secure=False,  # 프로덕션에서는 True로 설정
        samesite="lax"
    )
    
    return db_guest

@router.post("/login", response_model=GuestResponse)
def guest_login(
    response: Response, 
    db: Session = Depends(get_db),
    nickname: Optional[str] = None, 
    guest_uuid: Optional[str] = None
):
    guest = None
    
    # UUID로 로그인 시도
    if guest_uuid:
        try:
            uuid_obj = uuid.UUID(guest_uuid)
            guest = db.query(Guest).filter(Guest.uuid == uuid_obj).first()
        except (ValueError, TypeError):
            pass

    
    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게스트를 찾을 수 없습니다")
    
    # 마지막 로그인 시간 업데이트
    guest.last_login = datetime.datetime.utcnow()
    db.commit()
    db.refresh(guest)
    
    # 쿠키에 게스트 UUID 저장
    response.set_cookie(
        key="guest_uuid", 
        value=str(guest.uuid),
        httponly=True,
        max_age=3600 * 24 * 30,  # 30일
        secure=False,  # 프로덕션에서는 True로 설정
        samesite="lax"
    )
    
    return guest

@router.post("/logout")
def guest_logout(response: Response):
    # 쿠키 삭제
    response.delete_cookie(key="guest_uuid")
    return {"detail": "로그아웃 성공"}

@router.get("/me", response_model=GuestResponse)
def get_current_guest(guest_uuid: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    if not guest_uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증되지 않은 게스트")
    
    try:
        uuid_obj = uuid.UUID(guest_uuid)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 UUID")
    
    guest = db.query(Guest).filter(Guest.uuid == uuid_obj).first()
    if not guest:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="게스트를 찾을 수 없습니다")
    
    return guest

@router.get("/", response_model=List[GuestResponse], status_code=status.HTTP_200_OK)
def list_guests(db: Session = Depends(get_db)):
    guests = db.query(Guest).all()
    return guests

@router.get("/{guest_id}", response_model=GuestResponse, status_code=status.HTTP_200_OK)
def get_guest(guest_id: int, db: Session = Depends(get_db)):
    guest = db.query(Guest).filter(Guest.guest_id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게스트를 찾을 수 없습니다")
    return guest

@router.get("/uuid/{guest_uuid}", response_model=GuestResponse, status_code=status.HTTP_200_OK)
def get_guest_by_uuid(guest_uuid: uuid.UUID, db: Session = Depends(get_db)):
    guest = db.query(Guest).filter(Guest.uuid == guest_uuid).first()
    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게스트를 찾을 수 없습니다")
    
    return guest

@router.put("/{guest_id}", response_model=GuestResponse, status_code=status.HTTP_200_OK)
def update_guest(guest_id: int, guest_data: GuestUpdate, db: Session = Depends(get_db)):
    guest = db.query(Guest).filter(Guest.guest_id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게스트를 찾을 수 없습니다")
    if guest_data.nickname is not None:
        guest.nickname = guest_data.nickname
    db.commit()
    db.refresh(guest)
    return guest

@router.delete("/{guest_id}", status_code=status.HTTP_200_OK)
def delete_guest(guest_id: int, db: Session = Depends(get_db)):
    guest = db.query(Guest).filter(Guest.guest_id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게스트를 찾을 수 없습니다")
    db.delete(guest)
    db.commit()
    return {"detail": "게스트가 성공적으로 삭제되었습니다"} 