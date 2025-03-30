from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List
from models.gameroom import Gameroom
from models.guest import Guest
from schemas.gameroom import GameroomCreate, GameroomResponse, GameroomUpdate
from db.postgres import get_db

router = APIRouter(
    prefix="/gamerooms",
    tags=["gamerooms"],
)

@router.post("/", response_model=GameroomResponse, status_code=status.HTTP_201_CREATED)
def create_gameroom(room: GameroomCreate, db: Session = Depends(get_db)):
    # 생성자(Guest)가 존재하는지 검증
    creator = db.query(Guest).filter(Guest.guest_id == room.created_by).first()
    if not creator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="생성자(게스트)를 찾을 수 없습니다")
    db_room = Gameroom(**room.dict())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

@router.get("/", response_model=List[GameroomResponse], status_code=status.HTTP_200_OK)
def list_gamerooms(db: Session = Depends(get_db)):
    rooms = db.query(Gameroom).all()
    return rooms

@router.get("/{room_id}", response_model=GameroomResponse, status_code=status.HTTP_200_OK)
def get_gameroom(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Gameroom).filter(Gameroom.room_id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임룸을 찾을 수 없습니다")
    return room

@router.put("/{room_id}", response_model=GameroomResponse, status_code=status.HTTP_200_OK)
def update_gameroom(room_id: int, room_data: GameroomUpdate, db: Session = Depends(get_db)):
    room = db.query(Gameroom).filter(Gameroom.room_id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임룸을 찾을 수 없습니다")
    update_data = room_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(room, key, value)
    db.commit()
    db.refresh(room)
    return room

@router.delete("/{room_id}", status_code=status.HTTP_200_OK)
def delete_gameroom(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Gameroom).filter(Gameroom.room_id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임룸을 찾을 수 없습니다")
    db.delete(room)
    db.commit()
    return {"detail": "게임룸이 성공적으로 삭제되었습니다"} 