from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

# 기존 import
from db.postgres import get_db
from models.gameroom import Gameroom, GameStatus
from models.guest import Guest

# 새로 추가: GameroomParticipant, ParticipantStatus
from models.gameroom_participant import GameroomParticipant, ParticipantStatus

from schemas.gameroom import GameroomCreate, GameroomResponse, GameroomUpdate
from schemas.guest import GuestResponse  # 필요시 추가

router = APIRouter(
    prefix="/gamerooms",
    tags=["gamerooms"],
)


@router.get("/", response_model=List[GameroomResponse], status_code=status.HTTP_200_OK)
def list_gamerooms(db: Session = Depends(get_db)):
    rooms = db.query(Gameroom).filter(Gameroom.status != GameStatus.FINISHED).all()
    
    # 각 방에 대해 created_username 속성 추가
    for room in rooms:
        setattr(room, 'created_username', room.creator.nickname)
    
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
    
    # 방 생성자를 참가자로 등록
    creator_participant = GameroomParticipant(
        guest_id=guest.guest_id,
        room_id=db_room.room_id,
        status=ParticipantStatus.WAITING
    )
    db.add(creator_participant)
    db.commit()
    
    setattr(db_room, 'created_username', guest.nickname)
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
    
    setattr(db_room, 'created_username', db_room.creator.nickname)
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

    # 이미 참여중인지 + GameroomParticipant 생성 로직
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
    
    # 다른 방에 이미 참여 중인지 확인
    other_room_participation = db.query(GameroomParticipant).filter(
        GameroomParticipant.guest_id == guest.guest_id,
        GameroomParticipant.room_id != room.room_id,  # 현재 참여하려는 방이 아닌 다른 방
        GameroomParticipant.left_at.is_(None)  # 아직 나가지 않은 상태
    ).first()
    
    if other_room_participation:
        other_room = db.query(Gameroom).filter(Gameroom.room_id == other_room_participation.room_id).first()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"다른 방(방 ID: {other_room_participation.room_id})에 이미 참여 중입니다. 먼저 해당 방에서 나가야 합니다."
        )
    
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


@router.post("/{room_id}/leave", status_code=status.HTTP_200_OK)
def leave_gameroom(room_id: int, request: Request, db: Session = Depends(get_db)):
    # 쿠키에서 게스트 UUID 가져오기
    guest_uuid_str = request.cookies.get("kkua_guest_uuid")
    if not guest_uuid_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="게스트 UUID가 필요합니다. 쿠키에 kkua_guest_uuid가 없습니다."
        )
    
    # 문자열을 UUID로 변환
    try:
        guest_uuid = uuid.UUID(guest_uuid_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 UUID 형식입니다."
        )
    
    # Guest 조회
    guest = db.query(Guest).filter(Guest.uuid == guest_uuid).first()
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="유효하지 않은 게스트 UUID입니다."
        )
    
    # 게임룸 조회
    room = db.query(Gameroom).filter(Gameroom.room_id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임룸을 찾을 수 없습니다")
    
    # 참여 기록 확인
    participation = db.query(GameroomParticipant).filter(
        GameroomParticipant.guest_id == guest.guest_id,
        GameroomParticipant.room_id == room.room_id,
        GameroomParticipant.left_at.is_(None)  # 아직 나가지 않은 상태
    ).first()
    
    if not participation:
        # 방 생성자인지 확인
        if room.created_by == guest.guest_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="방장은 방을 나갈 수 없습니다. 방을 삭제해주세요."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이 방에 참여하고 있지 않습니다."
            )
    
    # 참여 기록 업데이트 (left_at 설정)
    from datetime import datetime
    participation.left_at = datetime.utcnow()
    participation.status = ParticipantStatus.LEFT
    
    # 인원수 감소
    if room.people > 0:
        room.people -= 1
    
    db.commit()
    
    return {"detail": f"게임룸({room.room_id})에서 성공적으로 나갔습니다."}


@router.post("/{room_id}/start", status_code=status.HTTP_200_OK)
def start_game(room_id: int, request: Request, db: Session = Depends(get_db)):
    # 쿠키에서 게스트 UUID 가져오기
    guest_uuid_str = request.cookies.get("kkua_guest_uuid")
    if not guest_uuid_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="게스트 UUID가 필요합니다. 쿠키에 kkua_guest_uuid가 없습니다."
        )
    
    # 문자열을 UUID로 변환
    try:
        guest_uuid = uuid.UUID(guest_uuid_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 UUID 형식입니다."
        )
    
    # Guest 조회
    guest = db.query(Guest).filter(Guest.uuid == guest_uuid).first()
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="유효하지 않은 게스트 UUID입니다."
        )
    
    # 게임룸 조회
    room = db.query(Gameroom).filter(Gameroom.room_id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임룸을 찾을 수 없습니다")
    
    # 방 생성자만 게임 시작 가능
    if room.created_by != guest.guest_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="방 생성자만 게임을 시작할 수 있습니다"
        )
    
    # 게임 상태 확인
    if room.status != GameStatus.WAITING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="대기 중인 방만 게임을 시작할 수 있습니다"
        )
    
    # 최소 인원 확인 (예: 최소 2명 이상)
    if room.people < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="게임을 시작하려면 최소 2명 이상의 참가자가 필요합니다"
        )
    
    # 게임 시작 처리
    room.status = GameStatus.PLAYING
    
    # 모든 참가자 상태 업데이트
    participants = db.query(GameroomParticipant).filter(
        GameroomParticipant.room_id == room.room_id,
        GameroomParticipant.left_at.is_(None)
    ).all()
    
    for participant in participants:
        participant.status = ParticipantStatus.PLAYING
    
    db.commit()
    db.refresh(room)
    
    return {"detail": f"게임룸({room.room_id})의 게임이 시작되었습니다."}


@router.post("/{room_id}/end", status_code=status.HTTP_200_OK)
def end_game(room_id: int, request: Request, db: Session = Depends(get_db)):
    # 쿠키에서 게스트 UUID 가져오기
    guest_uuid_str = request.cookies.get("kkua_guest_uuid")
    if not guest_uuid_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="게스트 UUID가 필요합니다. 쿠키에 kkua_guest_uuid가 없습니다."
        )
    
    # 문자열을 UUID로 변환
    try:
        guest_uuid = uuid.UUID(guest_uuid_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 UUID 형식입니다."
        )
    
    # Guest 조회
    guest = db.query(Guest).filter(Guest.uuid == guest_uuid).first()
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="유효하지 않은 게스트 UUID입니다."
        )
    
    # 게임룸 조회
    room = db.query(Gameroom).filter(Gameroom.room_id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임룸을 찾을 수 없습니다")
    
    # 방 생성자만 게임 종료 가능
    if room.created_by != guest.guest_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="방 생성자만 게임을 종료할 수 있습니다"
        )
    
    # 게임 상태 확인
    if room.status != GameStatus.PLAYING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="진행 중인 게임만 종료할 수 있습니다"
        )
    
    # 게임 종료 처리
    room.status = GameStatus.FINISHED
    
    # 모든 참가자 상태 업데이트
    participants = db.query(GameroomParticipant).filter(
        GameroomParticipant.room_id == room.room_id,
        GameroomParticipant.left_at.is_(None)
    ).all()
    
    for participant in participants:
        participant.status = ParticipantStatus.FINISHED
    
    db.commit()
    db.refresh(room)
    
    return {"detail": f"게임룸({room.room_id})의 게임이 종료되었습니다."}


@router.get("/{room_id}/participants", status_code=status.HTTP_200_OK)
def get_gameroom_participants(room_id: int, db: Session = Depends(get_db)):
    """특정 게임룸에 현재 참여 중인 모든 참가자 정보를 반환합니다."""
    
    # 게임룸 존재 확인
    room = db.query(Gameroom).filter(Gameroom.room_id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="게임룸을 찾을 수 없습니다")
    
    # 현재 참여 중인 참가자들 조회 (left_at이 NULL인 경우)
    participants = db.query(GameroomParticipant).filter(
        GameroomParticipant.room_id == room_id,
        GameroomParticipant.left_at.is_(None)
    ).all()
    
    # 결과 구성: 참가자 정보와 게스트 정보 모두 포함
    result = []
    for p in participants:
        guest_info = {
            "guest_id": p.guest.guest_id,
            "nickname": p.guest.nickname,
            "uuid": str(p.guest.uuid),
            "is_room_creator": (p.guest.guest_id == room.created_by)
        }
        
        participant_info = {
            "participant_id": p.id,
            "status": p.status.value,
            "joined_at": p.joined_at
        }
        
        result.append({
            "guest": guest_info,
            "participant": participant_info
        })
    
    return result


@router.get("/check-active-game", status_code=status.HTTP_200_OK)
def check_active_game(request: Request, guest_uuid_str: str = None, db: Session = Depends(get_db)):
    """
    유저가 현재 게임 중인지 확인하고, 게임 중이라면 해당 게임방 ID를 반환합니다.
    로비 페이지에 접근하기 전에 호출하여 필요시 게임방으로 리다이렉트합니다.
    """
    # 쿼리 파라미터에서 게스트 UUID 가져오기
    if not guest_uuid_str:
        guest_uuid_str = request.cookies.get("kkua_guest_uuid")
        if not guest_uuid_str:
            return {"redirect": False}
    
    # 문자열을 UUID 객체로 변환
    try:
        guest_uuid = uuid.UUID(guest_uuid_str)
    except ValueError:
        return {"redirect": False}
    
    # Guest 테이블에서 UUID로 게스트 검증
    guest = db.query(Guest).filter(Guest.uuid == guest_uuid).first()
    if not guest:
        return {"redirect": False}
    
    # 유저가 게임 중인지 확인
    from models.gameroom_participant import GameroomParticipant
    should_redirect, room_id = GameroomParticipant.should_redirect_to_game(db, guest.guest_id)
    
    if should_redirect:
        return {
            "redirect": True,
            "room_id": room_id
        }
    
    return {"redirect": False}
