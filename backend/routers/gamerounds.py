from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List
from models.gameround import Gameround
from models.gameroom import Gameroom
from models.guest import Guest
from schemas.gameround import GameroundCreate, GameroundResponse
from db.postgres import get_db

router = APIRouter(
    prefix="/gamerounds",
    tags=["gamerounds"],
)

@router.post("/", response_model=GameroundResponse, status_code=status.HTTP_201_CREATED)
def create_gameround(round: GameroundCreate, db: Session = Depends(get_db)):
    # 게임방과 게스트 존재 여부 확인
    room = db.query(Gameroom).filter(Gameroom.room_id == round.room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임룸을 찾을 수 없습니다")
    guest = db.query(Guest).filter(Guest.guest_id == round.guest_id).first()
    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게스트를 찾을 수 없습니다")
    db_round = Gameround(**round.dict())
    db.add(db_round)
    db.commit()
    db.refresh(db_round)
    return db_round

@router.get("/", response_model=List[GameroundResponse], status_code=status.HTTP_200_OK)
def list_gamerounds(db: Session = Depends(get_db)):
    rounds = db.query(Gameround).all()
    return rounds

@router.get("/{round_id}", response_model=GameroundResponse, status_code=status.HTTP_200_OK)
def get_gameround(round_id: int, db: Session = Depends(get_db)):
    round_obj = db.query(Gameround).filter(Gameround.round_id == round_id).first()
    if not round_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임 라운드를 찾을 수 없습니다")
    return round_obj

@router.delete("/{round_id}", status_code=status.HTTP_200_OK)
def delete_gameround(round_id: int, db: Session = Depends(get_db)):
    round_obj = db.query(Gameround).filter(Gameround.round_id == round_id).first()
    if not round_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임 라운드를 찾을 수 없습니다")
    db.delete(round_obj)
    db.commit()
    return {"detail": "게임 라운드가 성공적으로 삭제되었습니다"} 