from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List
from models.gameresult import Gameresult
from models.gameroom import Gameroom
from models.guest import Guest
from schemas.gameresult import GameresultCreate, GameresultResponse
from db.postgres import get_db

router = APIRouter(
    prefix="/gameresults",
    tags=["gameresults"],
)

@router.post("/", response_model=GameresultResponse, status_code=status.HTTP_201_CREATED)
def create_gameresult(result: GameresultCreate, db: Session = Depends(get_db)):
    # 게임방과 게스트 존재 여부 확인
    room = db.query(Gameroom).filter(Gameroom.room_id == result.room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임룸을 찾을 수 없습니다")
    guest = db.query(Guest).filter(Guest.guest_id == result.guest_id).first()
    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게스트를 찾을 수 없습니다")
    db_result = Gameresult(**result.dict())
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

@router.get("/", response_model=List[GameresultResponse], status_code=status.HTTP_200_OK)
def list_gameresults(db: Session = Depends(get_db)):
    results = db.query(Gameresult).all()
    return results

@router.get("/{result_id}", response_model=GameresultResponse, status_code=status.HTTP_200_OK)
def get_gameresult(result_id: int, db: Session = Depends(get_db)):
    result_obj = db.query(Gameresult).filter(Gameresult.result_id == result_id).first()
    if not result_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임 결과를 찾을 수 없습니다")
    return result_obj

@router.delete("/{result_id}", status_code=status.HTTP_200_OK)
def delete_gameresult(result_id: int, db: Session = Depends(get_db)):
    result_obj = db.query(Gameresult).filter(Gameresult.result_id == result_id).first()
    if not result_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임 결과를 찾을 수 없습니다")
    db.delete(result_obj)
    db.commit()
    return {"detail": "게임 결과가 성공적으로 삭제되었습니다"} 