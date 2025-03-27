from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Union
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

# PostgreSQL DB 연결 설정
DATABASE_URL = "postgresql://postgres:mysecretpassword@db:5432/mydb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# 방 정보 모델
class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)  # 방 제목
    people = Column(Integer, nullable=False)  # 현재 인원
    room_type = Column(String, nullable=False)  # 방 타입 (일반/스피드)
    max_people = Column(Integer, nullable=False, default=4)  # 최대 수용 인원
    playing = Column(Boolean, nullable=False, default=False)  # 게임 진행 상태

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()

# API 응답 모델
class RoomOut(BaseModel):
    id: int
    title: str
    people: int
    room_type: str
    max_people: int
    playing: bool

# API 요청 모델
class RoomCreate(BaseModel):
    title: str
    room_type: str
    max_people: int = 4

class RoomUpdate(BaseModel):
    title: str = None

# 방 목록 조회
@app.get("/rooms", response_model=List[RoomOut], status_code=status.HTTP_200_OK)
def read_rooms():
    db = SessionLocal()
    rooms = db.query(Room).all()
    db.close()
    return rooms

# 방 생성 
@app.post("/rooms", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(room: RoomCreate):
    db = SessionLocal()
    db_room = Room(**room.dict(), people=1, playing=False)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    db.close()
    return db_room

# 단일 방 조회
@app.get("/rooms/{room_id}", response_model=RoomOut, status_code=status.HTTP_200_OK)
def read_room(room_id: int):
    db = SessionLocal()
    room = db.query(Room).filter(Room.id == room_id).first()
    db.close()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
    return room

# 방 정보 수정 (제목만)
@app.put("/rooms/{room_id}", response_model=RoomOut, status_code=status.HTTP_200_OK)
def update_room(room_id: int, room: RoomUpdate):
    db = SessionLocal()
    db_room = db.query(Room).filter(Room.id == room_id).first()
    
    if not db_room:
        db.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
    
    if room.title is not None:
        db_room.title = room.title
    
    db.commit()
    db.refresh(db_room)
    db.close()
    return db_room

# 방 삭제
@app.delete("/rooms/{room_id}", response_model=dict, status_code=status.HTTP_200_OK)
def delete_room(room_id: int):
    db = SessionLocal()
    room = db.query(Room).filter(Room.id == room_id).first()
    
    if not room:
        db.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
    
    db.delete(room)
    db.commit()
    db.close()
    return {"message": "방이 성공적으로 삭제되었습니다"}

# 방 참여
@app.post("/rooms/{room_id}/join", response_model=RoomOut, status_code=status.HTTP_200_OK)
def join_room(room_id: int):
    db = SessionLocal()
    db_room = db.query(Room).filter(Room.id == room_id).first()
    
    if not db_room:
        db.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
        
    if db_room.people >= db_room.max_people:
        db.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"방이 이미 가득 찼습니다 (최대 {db_room.max_people}명)")
        
    db_room.people += 1
    db.commit()
    db.refresh(db_room)
    db.close()
    return db_room

# 방 나가기
@app.post("/rooms/{room_id}/leave", response_model=Union[RoomOut, dict], status_code=status.HTTP_200_OK)
def leave_room(room_id: int):
    db = SessionLocal()
    db_room = db.query(Room).filter(Room.id == room_id).first()
    
    if not db_room:
        db.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
        
    if db_room.people > 0:
        db_room.people -= 1
        
        if db_room.people == 0:
            db.delete(db_room)
            db.commit()
            db.close()
            return {"message": "모든 참여자가 나가서 방이 자동으로 삭제되었습니다"}
        
        db.commit()
        db.refresh(db_room)
        
    db.close()
    return db_room

# 게임 시작
@app.post("/rooms/{room_id}/play", response_model=RoomOut, status_code=status.HTTP_200_OK)
def start_game(room_id: int):
    db = SessionLocal()
    db_room = db.query(Room).filter(Room.id == room_id).first()
    
    if not db_room:
        db.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
    
    if db_room.playing:
        db.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 게임이 시작되었습니다")
    
    db_room.playing = True
    db.commit()
    db.refresh(db_room)
    db.close()
    return db_room

# 게임 종료
@app.post("/rooms/{room_id}/end", response_model=RoomOut, status_code=status.HTTP_200_OK)
def end_game(room_id: int):
    db = SessionLocal()
    db_room = db.query(Room).filter(Room.id == room_id).first()
    
    if not db_room:
        db.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
    
    if not db_room.playing:
        db.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 게임이 종료되었습니다")
    
    db_room.playing = False
    db.commit()
    db.refresh(db_room)
    db.close()
    return db_room

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
