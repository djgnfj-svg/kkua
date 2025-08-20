from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Dict, Optional

from db.postgres import get_db
from services.gameroom_service import GameroomService
from middleware.auth_middleware import get_current_guest
from models.guest_model import Guest
from schemas.gameroom_schema import (
    GameroomResponse,
    CreateGameroomRequest,
    GameroomUpdate,
    GameroomListResponse,
    GameroomDetailResponse,
)

router = APIRouter(
    prefix="/gamerooms",
    tags=["gamerooms"],
)


def get_gameroom_service(db: Session = Depends(get_db)) -> GameroomService:
    return GameroomService(db)


@router.get("/", response_model=GameroomListResponse)
def list_gamerooms(
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    service: GameroomService = Depends(get_gameroom_service),
) -> GameroomListResponse:
    """게임룸 목록을 조회합니다. 필터링 옵션을 제공합니다."""
    rooms, total = service.list_gamerooms(status=status, limit=limit, offset=offset)
    return {"rooms": rooms, "total": total}


@router.post("/", response_model=GameroomResponse, status_code=status.HTTP_201_CREATED)
async def create_gameroom(
    create_data: CreateGameroomRequest,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
) -> GameroomResponse:
    """게임룸을 생성합니다."""
    return service.create_gameroom(create_data.dict(), guest.guest_id)


@router.get("/{room_id}", response_model=GameroomDetailResponse)
def get_gameroom(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
) -> GameroomDetailResponse:
    """게임룸 상세 정보를 조회합니다. 참가자만 조회할 수 있습니다."""
    room = service.get_gameroom(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="게임룸을 찾을 수 없습니다")

    participants = service.get_participants(room_id)

    # 현재 사용자가 방 참가자인지 확인
    is_participant = any(p.get("guest_id") == guest.guest_id for p in participants)

    # 방장인지 확인
    is_creator = room.created_by == guest.guest_id

    if not (is_participant or is_creator):
        raise HTTPException(
            status_code=403,
            detail="이 방에 참가하지 않은 사용자는 방 정보를 조회할 수 없습니다",
        )

    return {"room": room, "participants": participants}


@router.patch("/{room_id}", response_model=GameroomResponse)
def update_gameroom(
    room_id: int,
    update_data: GameroomUpdate,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
) -> GameroomResponse:
    """게임룸 정보를 업데이트합니다. 방장만 수정할 수 있습니다."""
    update_dict = update_data.dict(exclude_unset=True)
    return service.update_gameroom(room_id, update_dict)


@router.delete("/{room_id}", status_code=status.HTTP_200_OK)
def delete_gameroom(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
) -> Dict[str, str]:
    """게임룸을 삭제합니다. 방장만 삭제할 수 있습니다."""
    success = service.delete_gameroom(room_id)
    if not success:
        raise HTTPException(status_code=404, detail="게임룸을 찾을 수 없습니다")

    return {"message": "게임룸이 삭제되었습니다"}


@router.get("/{room_id}/is-owner")
def check_room_owner(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
) -> Dict[str, bool]:
    """현재 사용자가 방장인지 확인합니다."""
    room = service.get_gameroom(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="게임룸을 찾을 수 없습니다")
    
    is_owner = room.created_by == guest.guest_id
    return {"is_owner": is_owner}


@router.post("/{room_id}/join")
async def join_gameroom(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
) -> Dict[str, str]:
    """게임룸에 참가합니다."""
    try:
        result = await service.join_gameroom(room_id, guest)
        return {"message": result.message}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{room_id}/leave")
def leave_gameroom(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
) -> Dict[str, str]:
    """게임룸에서 나갑니다."""
    try:
        result = service.leave_gameroom(room_id, guest)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{room_id}/start")
def start_game(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
) -> Dict[str, str]:
    """게임을 시작합니다. 방장만 시작할 수 있습니다."""
    room = service.get_gameroom(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="게임룸을 찾을 수 없습니다")
    
    if room.created_by != guest.guest_id:
        raise HTTPException(status_code=403, detail="방장만 게임을 시작할 수 있습니다")
    
    try:
        # 게임 시작 로직 (향후 구현)
        return {"message": "게임이 시작되었습니다"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{room_id}/game/state")
async def get_game_state(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
) -> Dict:
    """Redis에서 게임 상태를 조회합니다."""
    try:
        # 게임룸 존재 확인
        room = service.get_gameroom(room_id)
        if not room:
            raise HTTPException(status_code=404, detail="게임룸을 찾을 수 없습니다")
        
        # 참가자 확인
        participant = service.repository.find_participant(room_id, guest.guest_id)
        if not participant:
            raise HTTPException(status_code=403, detail="게임에 참가하지 않은 사용자입니다")
        
        # Redis에서 게임 상태 조회
        from services.redis_game_service import get_redis_game_service
        redis_service = await get_redis_game_service()
        
        game_state = await redis_service.get_game_state(room_id)
        if not game_state:
            raise HTTPException(status_code=404, detail="게임 상태를 찾을 수 없습니다")
        
        return game_state
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"게임 상태 조회 중 오류 발생: {str(e)}")


@router.post("/{room_id}/game/submit-word")
async def submit_word(
    room_id: int,
    word_data: Dict[str, str],
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
) -> Dict:
    """Redis 게임에 단어를 제출합니다."""
    try:
        # 게임룸 존재 확인
        room = service.get_gameroom(room_id)
        if not room:
            raise HTTPException(status_code=404, detail="게임룸을 찾을 수 없습니다")
        
        # 참가자 확인
        participant = service.repository.find_participant(room_id, guest.guest_id)
        if not participant:
            raise HTTPException(status_code=403, detail="게임에 참가하지 않은 사용자입니다")
        
        # 단어 추출
        word = word_data.get("word", "").strip()
        if not word:
            raise HTTPException(status_code=400, detail="단어를 입력해주세요")
        
        # Redis에서 단어 제출
        from services.redis_game_service import get_redis_game_service
        redis_service = await get_redis_game_service()
        
        result = await redis_service.submit_word(room_id, guest.guest_id, word)
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("message", "단어 제출에 실패했습니다"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"단어 제출 중 오류 발생: {str(e)}")
