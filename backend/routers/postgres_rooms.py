from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Union
from sqlalchemy.orm import Session
from models.room import Room
from models.guest import Guest
from schemas.room import RoomOut, RoomCreate, RoomUpdate
from db.postgres import get_db

router = APIRouter(
    prefix="/api/rooms",
    tags=["postgres-rooms"],
)

# 방 목록 조회
@router.get("/", response_model=List[RoomOut], status_code=status.HTTP_200_OK)
def read_rooms(db: Session = Depends(get_db)):
    rooms = db.query(Room).all()
    return rooms

# 방 생성 
@router.post("/", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(room: RoomCreate, db: Session = Depends(get_db)):
    # Guest 존재 여부 확인 (옵셔널)
    if room.created_by:
        guest = db.query(Guest).filter(Guest.guest_id == room.created_by).first()
        if not guest:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게스트를 찾을 수 없습니다")
    
    db_room = Room(**room.dict(), people=1, playing=False)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

# 단일 방 조회
@router.get("/{room_id}", response_model=RoomOut, status_code=status.HTTP_200_OK)
def read_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
    return room

# 방 정보 수정 (제목만)
@router.put("/{room_id}", response_model=RoomOut, status_code=status.HTTP_200_OK)
def update_room(room_id: int, room: RoomUpdate, db: Session = Depends(get_db)):
    db_room = db.query(Room).filter(Room.id == room_id).first()
    
    if not db_room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
    
    # 수정 가능한 필드 업데이트
    update_data = room.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_room, key, value)
    
    db.commit()
    db.refresh(db_room)
    return db_room

# 방 삭제
@router.delete("/{room_id}", response_model=dict, status_code=status.HTTP_200_OK)
def delete_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
    
    db.delete(room)
    db.commit()
    return {"message": "방이 성공적으로 삭제되었습니다"}

# 방 참여
@router.post("/{room_id}/join", response_model=RoomOut, status_code=status.HTTP_200_OK)
def join_room(room_id: int, db: Session = Depends(get_db)):
    db_room = db.query(Room).filter(Room.id == room_id).first()
    
    if not db_room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
        
    if db_room.people >= db_room.max_people:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"방이 이미 가득 찼습니다 (최대 {db_room.max_people}명)")
        
    db_room.people += 1
    db.commit()
    db.refresh(db_room)
    return db_room

# 방 나가기
@router.post("/{room_id}/leave", response_model=Union[RoomOut, dict], status_code=status.HTTP_200_OK)
def leave_room(room_id: int, db: Session = Depends(get_db)):
    db_room = db.query(Room).filter(Room.id == room_id).first()
    
    if not db_room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
        
    if db_room.people > 0:
        db_room.people -= 1
        
        if db_room.people == 0:
            db.delete(db_room)
            db.commit()
            return {"message": "모든 참여자가 나가서 방이 자동으로 삭제되었습니다"}
        
        db.commit()
        db.refresh(db_room)
        
    return db_room

# 게임 시작
@router.post("/{room_id}/play", response_model=RoomOut, status_code=status.HTTP_200_OK)
def start_game(room_id: int, db: Session = Depends(get_db)):
    db_room = db.query(Room).filter(Room.id == room_id).first()
    
    if not db_room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
    
    if db_room.playing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 게임이 시작되었습니다")
    
    db_room.playing = True
    db.commit()
    db.refresh(db_room)
    return db_room

# 게임 종료
@router.post("/{room_id}/end", response_model=RoomOut, status_code=status.HTTP_200_OK)
def end_game(room_id: int, db: Session = Depends(get_db)):
    db_room = db.query(Room).filter(Room.id == room_id).first()
    
    if not db_room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
    
    if not db_room.playing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 게임이 종료되었습니다")
    
    db_room.playing = False
    db.commit()
    db.refresh(db_room)
    return db_room 