from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Union
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

# DB 연결: Docker에서 실행한 PostgreSQL (DB 컨테이너가 localhost:5432에 매핑되어 있다고 가정)
DATABASE_URL = "postgresql://postgres:mysecretpassword@db:5432/mydb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# SQLAlchemy 모델
class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    people = Column(Integer, nullable=False)
    level = Column(String, nullable=False)
    playing = Column(Boolean, nullable=False, default=False)  # 플레이 중 여부

# 테이블이 없으면 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 응답 모델
class RoomOut(BaseModel):
    id: int
    title: str
    people: int
    level: str
    playing: bool

# 요청 모델 수정 - 제목만 변경 가능하도록
class RoomCreate(BaseModel):
    title: str
    level: str

class RoomUpdate(BaseModel):
    title: str = None
    # level, people, playing 필드는 직접 수정할 수 없음

@app.get("/rooms", response_model=List[RoomOut], status_code=status.HTTP_200_OK)
def read_rooms():
    db = SessionLocal()
    rooms = db.query(Room).all()
    db.close()
    return rooms

# 생성(Create) 기능 수정 - 생성자가 자동으로 참여하도록 people=1로 설정
@app.post("/rooms", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(room: RoomCreate):
    db = SessionLocal()
    db_room = Room(**room.dict(), people=1, playing=False)  # people을 1로 초기화 (생성자 자동 참여)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    db.close()
    return db_room

# 단일 방 조회 기능
@app.get("/rooms/{room_id}", response_model=RoomOut, status_code=status.HTTP_200_OK)
def read_room(room_id: int):
    db = SessionLocal()
    room = db.query(Room).filter(Room.id == room_id).first()
    db.close()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
    return room

# 업데이트(Update) 기능 - 제목만 수정 가능하도록 제한
@app.put("/rooms/{room_id}", response_model=RoomOut, status_code=status.HTTP_200_OK)
def update_room(room_id: int, room: RoomUpdate):
    db = SessionLocal()
    db_room = db.query(Room).filter(Room.id == room_id).first()
    
    if not db_room:
        db.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
    
    # 제목만 업데이트
    if room.title is not None:
        db_room.title = room.title
    
    db.commit()
    db.refresh(db_room)
    db.close()
    return db_room

# 삭제(Delete) 기능 추가
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

# 참여(Join) 기능 추가
@app.post("/rooms/{room_id}/join", response_model=RoomOut, status_code=status.HTTP_200_OK)
def join_room(room_id: int):
    db = SessionLocal()
    db_room = db.query(Room).filter(Room.id == room_id).first()
    
    if not db_room:
        db.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
        
    # 최대 인원(4명) 체크
    if db_room.people >= 4:
        db.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="방이 이미 가득 찼습니다 (최대 4명)")
        
    db_room.people += 1  # 참여자 수 1 증가
    db.commit()
    db.refresh(db_room)
    db.close()
    return db_room

# 참여 취소(Leave) 기능 수정 - 0명이 되면 방 자동 삭제
@app.post("/rooms/{room_id}/leave", response_model=Union[RoomOut, dict], status_code=status.HTTP_200_OK)
def leave_room(room_id: int):
    db = SessionLocal()
    db_room = db.query(Room).filter(Room.id == room_id).first()
    
    if not db_room:
        db.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
        
    if db_room.people > 0:
        db_room.people -= 1
        
        # 참여자가 0명이 되면 방 자동 삭제
        if db_room.people == 0:
            db.delete(db_room)
            db.commit()
            db.close()
            return {"message": "모든 참여자가 나가서 방이 자동으로 삭제되었습니다"}
        
        db.commit()
        db.refresh(db_room)
        
    db.close()
    return db_room

# 게임 시작 API - URL 변경 (/start -> /play)
@app.post("/rooms/{room_id}/play", response_model=RoomOut, status_code=status.HTTP_200_OK)
def start_game(room_id: int):
    db = SessionLocal()
    db_room = db.query(Room).filter(Room.id == room_id).first()
    
    if not db_room:
        db.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
    
    # 이미 플레이 중인지 확인
    if db_room.playing:
        db.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 게임이 시작되었습니다")
    
    # 플레이 중 상태로 변경
    db_room.playing = True
    db.commit()
    db.refresh(db_room)
    db.close()
    return db_room

# 게임 종료 API 추가
@app.post("/rooms/{room_id}/end", response_model=RoomOut, status_code=status.HTTP_200_OK)
def end_game(room_id: int):
    db = SessionLocal()
    db_room = db.query(Room).filter(Room.id == room_id).first()
    
    if not db_room:
        db.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="방을 찾을 수 없습니다")
    
    # 이미 게임이 종료되었는지 확인
    if not db_room.playing:
        db.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 게임이 종료되었습니다")
    
    # 플레이 종료 상태로 변경
    db_room.playing = False
    db.commit()
    db.refresh(db_room)
    db.close()
    return db_room

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
