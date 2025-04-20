from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid

from db.postgres import get_db
from repositories.gameroom_repository import GameroomRepository
from repositories.guest_repository import GuestRepository
from services.gameroom_service import GameroomService
from schemas.gameroom_schema import (
    GameroomResponse, GameroomListResponse, JoinGameroomResponse,
    CreateGameroomRequest, GameroomDetailResponse
)

router = APIRouter(
    prefix="/gamerooms",
    tags=["gamerooms"],
)

def get_gameroom_service(db: Session = Depends(get_db)) -> GameroomService:
    gameroom_repo = GameroomRepository(db)
    guest_repo = GuestRepository(db)
    return GameroomService(gameroom_repo, guest_repo)

@router.get("/", response_model=List[GameroomResponse], status_code=status.HTTP_200_OK)
def list_gamerooms(service: GameroomService = Depends(get_gameroom_service)):
    return service.list_gamerooms()

@router.post("/", response_model=GameroomResponse)
async def create_gameroom(
    request: Request,
    title: str = None,
    max_players: int = 2,
    game_mode: str = "arcade",
    time_limit: int = 120,
    service: GameroomService = Depends(get_gameroom_service)
) -> GameroomResponse:
    """
    게임룸을 생성합니다.
    """
    print(f"게임룸 생성 요청 - 쿼리 파라미터: title={title}, max_players={max_players}, game_mode={game_mode}")
    
    # 본문에서 게임룸 정보 가져오기 시도
    body = {}
    try:
        body = await request.json()
        print("요청 본문:", body)
    except:
        pass
    
    # 쿠키에서 UUID 가져오기
    guest_uuid = request.cookies.get("kkua_guest_uuid")
    
    # UUID 유효성 검사
    if guest_uuid == "undefined" or not guest_uuid:
        raise HTTPException(status_code=400, detail="유효한 게스트 UUID가 필요합니다")
    
    # 요청 파라미터 준비 (쿼리 파라미터 + 본문 데이터)
    room_data = {
        "title": body.get("title", title) or "새 게임",
        "max_players": body.get("max_players", max_players),
        "game_mode": body.get("game_mode", game_mode),
        "time_limit": body.get("time_limit", time_limit)
    }
    
    try:
        # UUID 검증 및 객체 변환
        try:
            uuid_obj = uuid.UUID(guest_uuid) if isinstance(guest_uuid, str) else guest_uuid
        except ValueError:
            raise HTTPException(status_code=400, detail=f"유효하지 않은 UUID 형식: {guest_uuid}")
            
        # 게스트 찾기
        guest = service.guest_repository.find_by_uuid(uuid_obj)
        if not guest:
            raise HTTPException(status_code=404, detail="게스트를 찾을 수 없습니다")
        
        # guest_id 추가
        room_data["created_by"] = guest.guest_id
        
        # 방 생성
        new_room = service.repository.create(room_data, guest.guest_id)
        
        return GameroomResponse(
            room_id=new_room.room_id,
            title=new_room.title,
            max_players=new_room.max_players,
            game_mode=new_room.game_mode,
            created_by=new_room.created_by,
            created_username=guest.nickname,
            status=new_room.status.value,
            participant_count=1,
            time_limit=new_room.time_limit
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"잘못된 UUID 형식: {str(e)}")
    except Exception as e:
        print(f"방 생성 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"방 생성 실패: {str(e)}")

@router.post("/{room_id}/join", status_code=status.HTTP_200_OK)
def join_gameroom(
    room_id: int, 
    request: Request, 
    service: GameroomService = Depends(get_gameroom_service)
):
    return service.join_gameroom(room_id, request)

@router.post("/{room_id}/leave", status_code=status.HTTP_200_OK)
def leave_gameroom(
    room_id: int, 
    request: Request, 
    service: GameroomService = Depends(get_gameroom_service)
):
    return service.leave_gameroom(room_id, request)


@router.get("/{room_id}/participants", status_code=status.HTTP_200_OK)
def get_gameroom_participants(
    room_id: int, 
    service: GameroomService = Depends(get_gameroom_service)
):
    """
    게임룸의 참가자 목록과 방 정보를 함께 반환합니다.
    """
    # 방 정보 조회
    room = service.repository.find_by_id(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="게임룸을 찾을 수 없습니다")
    
    # 참가자 정보 조회
    participants = service.get_participants(room_id)
    
    # 참가자 수
    participant_count = len(participants)
    
    # 방장 닉네임 찾기 (참가자 정보에서)
    creator_name = "알 수 없음"
    for participant in participants:
        if participant["guest"]["is_room_creator"]:
            creator_name = participant["guest"]["nickname"]
            break
    
    # 응답에 room_info 추가하여 반환
    return {
        "participants": participants,
        "room_info": {
            "room_id": room.room_id,
            "title": room.title,
            "max_players": room.max_players,
            "game_mode": room.game_mode,
            "time_limit": room.time_limit,
            "created_by": room.created_by,
            "created_username": creator_name,
            "status": room.status.value,
            "participant_count": participant_count
        }
    }

@router.get("/check-active-game", status_code=status.HTTP_200_OK)
def check_active_game(
    request: Request, 
    guest_uuid_str: str = None, 
    service: GameroomService = Depends(get_gameroom_service)
):
    return service.check_active_game(request, guest_uuid_str)