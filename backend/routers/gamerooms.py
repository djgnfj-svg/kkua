from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from typing import List
import uuid

# 기존 import
from db.postgres import get_db
from models.gameroom import Gameroom, GameStatus
from models.guest import Guest

# 새로 추가: GameroomParticipant, ParticipantStatus
from models.gameroom_participant import GameroomParticipant, ParticipantStatus

from schemas.gameroom import GameroomCreate, GameroomResponse, GameroomUpdate

router = APIRouter(
    prefix="/gamerooms",
    tags=["gamerooms"],
)


@router.get("/", response_model=List[GameroomResponse], status_code=status.HTTP_200_OK)
def list_gamerooms(db: Session = Depends(get_db)):
    rooms = db.query(Gameroom).all()
    return rooms


@router.post("/", response_model=GameroomResponse, status_code=status.HTTP_201_CREATED)
def create_gameroom(
    request: Request,
    title: str = None,
    max_players: int = None,
    game_mode: str = None,
    time_limit: int = None,
    db: Session = Depends(get_db)
):
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
        
    # 이미 생성한 방이 있는지 확인 (게임이 끝나지 않은 방)
    existing_room = db.query(Gameroom).filter(
        Gameroom.created_by == guest.guest_id,
        Gameroom.status != GameStatus.FINISHED
    ).first()
    if existing_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 생성한 방이 있습니다. 새로운 방을 만들기 전에 기존 방을 삭제해주세요."
        )

    # 기본값 설정
    room_data = {
        "title": title if title is not None else "새로운 방",
        "max_players": max_players if max_players is not None else 4,
        "game_mode": game_mode if game_mode is not None else "normal",
        "time_limit": time_limit if time_limit is not None else 60,
        "created_by": guest.guest_id,
        "status": GameStatus.WAITING
    }
    
    db_room = Gameroom(**room_data)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room


@router.patch("/{room_id}", response_model=GameroomResponse, status_code=status.HTTP_200_OK)
def update_gameroom(
    room_id: int, 
    request: Request, 
    title: str = None, 
    max_players: int = None, 
    game_mode: str = None, 
    time_limit: int = None, 
    db: Session = Depends(get_db)
):
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

    # 게임룸 조회
    db_room = db.query(Gameroom).filter(Gameroom.room_id == room_id).first()
    if not db_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게임룸을 찾을 수 없습니다"
        )
    
    # 방 생성자만 수정 가능
    if db_room.created_by != guest.guest_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="방 생성자만 수정할 수 있습니다"
        )
    
    # 게임중인 방은 수정 불가
    if db_room.status == GameStatus.PLAYING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="게임 진행 중인 방은 수정할 수 없습니다"
        )

    # 업데이트할 값 설정
    if title is not None:
        db_room.title = title
    if max_players is not None:
        db_room.max_players = max_players
    if game_mode is not None:
        db_room.game_mode = game_mode
    if time_limit is not None:
        db_room.time_limit = time_limit

    db.commit()
    db.refresh(db_room)
    return db_room


@router.delete("/{room_id}", status_code=status.HTTP_200_OK)
def delete_gameroom(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Gameroom).filter(Gameroom.room_id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임룸을 찾을 수 없습니다")
    room.status = GameStatus.FINISHED
    db.commit()
    return {"detail": "게임룸이 성공적으로 종료되었습니다"}


@router.post("/{room_id}/join", status_code=status.HTTP_200_OK)
def join_gameroom(room_id: int, request: Request, db: Session = Depends(get_db)):
    # 1. 쿠키에서 게스트 UUID 가져오기
    guest_uuid_str = request.cookies.get("kkua_guest_uuid")
    if not guest_uuid_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="게스트 UUID가 필요합니다. 쿠키에 kkua_guest_uuid가 없습니다."
        )

    # 2. 문자열을 UUID로 변환
    try:
        guest_uuid = uuid.UUID(guest_uuid_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 UUID 형식입니다."
        )

    # 3. Guest 조회
    guest = db.query(Guest).filter(Guest.uuid == guest_uuid).first()
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="유효하지 않은 게스트 UUID입니다."
        )
    
    # 4. 게임룸 조회
    room = db.query(Gameroom).filter(Gameroom.room_id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임룸을 찾을 수 없습니다")
    
    # 이미 방 생성자인지 확인
    if room.created_by == guest.guest_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 해당 방의 생성자입니다."
        )
    
    # 최대 인원 초과 확인
    if room.people >= room.max_players:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="방이 가득 찼습니다."
        )
    
    # 게임 진행중인지 확인
    if room.status == GameStatus.PLAYING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="게임이 이미 시작되었습니다."
        )

    # 게임이 종료되었는지 확인
    if room.status == GameStatus.FINISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="종료된 게임입니다."
        )

    # ▶▶ 추가된 부분: 이미 참여중인지 + GameroomParticipant 생성 로직 ◀◀
    existing_participation = db.query(GameroomParticipant).filter(
        GameroomParticipant.guest_id == guest.guest_id,
        GameroomParticipant.room_id == room.room_id,
        GameroomParticipant.left_at.is_(None)  # 아직 나가지 않은 상태
    ).first()
    if existing_participation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 이 방에 참여중입니다."
        )
    
    # (선택) 한 유저가 동시에 한 방만 허용하려면,
    # 다른 방에 참여중인 레코드(left_at이 NULL)를 찾아서 막는 로직 추가

    # 새로운 참가 레코드
    new_participation = GameroomParticipant(
        guest_id=guest.guest_id,
        room_id=room.room_id,
        status=ParticipantStatus.WAITING  # 기본 상태
    )
    db.add(new_participation)

    # 인원수 증가
    room.people += 1

    db.commit()
    db.refresh(room)
    db.refresh(new_participation)

    return {"detail": f"게임룸({room.room_id})에 성공적으로 참여하였습니다."}
