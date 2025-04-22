from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from db.postgres import get_db
from repositories.gameroom_repository import GameroomRepository
from repositories.guest_repository import GuestRepository
from services.gameroom_service import GameroomService
from schemas.gameroom_schema import (
    GameroomResponse, CreateGameroomRequest, GameroomUpdate, GameroomListResponse
)
from schemas.gameroom_actions_schema import GameroomDetailResponse

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
    service: GameroomService = Depends(get_gameroom_service)
) -> GameroomListResponse:
    """게임룸 목록을 조회합니다. 필터링 옵션을 제공합니다."""
    rooms, total = service.list_gamerooms(status=status, limit=limit, offset=offset)
    return {
        "rooms": rooms,
        "total": total
    }

@router.post("/", response_model=GameroomResponse, status_code=status.HTTP_201_CREATED)
def create_gameroom(
    request: Request,
    create_data: CreateGameroomRequest,
    service: GameroomService = Depends(get_gameroom_service)
) -> GameroomResponse:
    """게임룸을 생성합니다."""
    guest_uuid = request.cookies.get("kkua_guest_uuid")
    if not guest_uuid:
        raise HTTPException(status_code=400, detail="유효한 게스트 UUID가 필요합니다")
    
    return service.create_gameroom(create_data.dict(), guest_uuid)

@router.get("/{room_id}", response_model=GameroomDetailResponse)
def get_gameroom(
    room_id: int,
    service: GameroomService = Depends(get_gameroom_service)
) -> GameroomDetailResponse:
    """게임룸 상세 정보를 조회합니다."""
    room = service.get_gameroom(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="게임룸을 찾을 수 없습니다")
    
    participants = service.get_participants(room_id)
    return {
        "room": room,
        "participants": participants
    }

@router.patch("/{room_id}", response_model=GameroomResponse)
def update_gameroom(
    room_id: int,
    update_data: GameroomUpdate,
    request: Request,
    service: GameroomService = Depends(get_gameroom_service)
) -> GameroomResponse:
    """게임룸 정보를 업데이트합니다. 방장만 수정할 수 있습니다."""
    guest_uuid = request.cookies.get("kkua_guest_uuid")
    if not guest_uuid:
        raise HTTPException(status_code=400, detail="유효한 게스트 UUID가 필요합니다")
    
    update_dict = update_data.dict(exclude_unset=True)
    return service.update_gameroom(room_id, update_dict)

@router.delete("/{room_id}", status_code=status.HTTP_200_OK)
def delete_gameroom(
    room_id: int,
    request: Request,
    service: GameroomService = Depends(get_gameroom_service)
) -> Dict[str, str]:
    """게임룸을 삭제합니다. 방장만 삭제할 수 있습니다."""
    guest_uuid = request.cookies.get("kkua_guest_uuid")
    if not guest_uuid:
        raise HTTPException(status_code=400, detail="유효한 게스트 UUID가 필요합니다")
    
    success = service.delete_gameroom(room_id)
    if not success:
        raise HTTPException(status_code=404, detail="게임룸을 찾을 수 없습니다")
    
    return {"message": "게임룸이 삭제되었습니다"}