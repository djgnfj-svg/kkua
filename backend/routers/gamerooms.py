from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from typing import List
from models.gameroom import Gameroom
from models.guest import Guest
from schemas.gameroom import GameroomCreate, GameroomResponse, GameroomUpdate
from db.postgres import get_db
import uuid
from models.gameroom import GameStatus

router = APIRouter(
    prefix="/gamerooms",
    tags=["gamerooms"],
)

@router.get("/", response_model=List[GameroomResponse], status_code=status.HTTP_200_OK)
def list_gamerooms(db: Session = Depends(get_db)):
    rooms = db.query(Gameroom).all()
    return rooms


@router.post("/", response_model=GameroomResponse, status_code=status.HTTP_201_CREATED)
def create_gameroom(request: Request, room: GameroomCreate, db: Session = Depends(get_db)):
    # 쿠키에서 게스트 UUID 가져오기
    guest_uuid_str = request.cookies.get("kkua_guest_uuid")
    
    if not guest_uuid_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="게스트 UUID가 필요합니다. 쿠키에 kkua_guest_uuid가 없습니다."
        )
    
    # 문자열을 UUID 객체로 변환
    try:
        guest_uuid = uuid.UUID(guest_uuid_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 UUID 형식입니다."
        )
    
    # Guest 테이블에서 UUID로 게스트 검증
    guest = db.query(Guest).filter(Guest.uuid == guest_uuid).first()
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="유효하지 않은 게스트 UUID입니다."
        )
        
    # 이미 생성한 방이 있는지 확인
    existing_room = db.query(Gameroom).filter(
        Gameroom.created_by == guest.guest_id,
        Gameroom.status != GameStatus.FINISHED  # 문자열 대신 Enum 객체 사용
    ).first()
    
    if existing_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 생성한 방이 있습니다. 새로운 방을 만들기 전에 기존 방을 삭제해주세요."
        )
    
    # 게임룸 생성
    room_data = room.dict(exclude={"uuid"})
    # 게스트 ID 설정
    room_data["created_by"] = guest.guest_id
    # 초기 상태를 대기중으로 설정
    room_data["status"] = GameStatus.WAITING
    
    db_room = Gameroom(**room_data)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room


@router.delete("/{room_id}", status_code=status.HTTP_200_OK)
def delete_gameroom(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Gameroom).filter(Gameroom.room_id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임룸을 찾을 수 없습니다")
    room.status = GameStatus.FINISHED  # 문자열 대신 Enum 객체 사용
    db.commit()
    return {"detail": "게임룸이 성공적으로 종료되었습니다"}