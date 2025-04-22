from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from db.postgres import get_db
from repositories.gameroom_repository import GameroomRepository
from repositories.guest_repository import GuestRepository
from services.gameroom_service import GameroomService
from schemas.gameroom_schema import (
    GameroomResponse, CreateGameroomRequest, GameroomDetailResponse, GameroomUpdate
)

router = APIRouter(
    prefix="/gamerooms",
    tags=["gamerooms"],
)

def get_gameroom_service(db: Session = Depends(get_db)) -> GameroomService:
    gameroom_repo = GameroomRepository(db)
    guest_repo = GuestRepository(db)
    return GameroomService(gameroom_repo, guest_repo)

@router.get("/", response_model=List[GameroomResponse])
def list_gamerooms(
    status: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    service: GameroomService = Depends(get_gameroom_service)
) -> List[GameroomResponse]:
    """게임룸 목록을 조회합니다. 필터링 및 정렬 옵션을 제공합니다."""
    return service.list_gamerooms(status, sort_by, sort_order)

@router.post("/", response_model=GameroomResponse)
def create_gameroom(
    request: Request,
    create_data: CreateGameroomRequest,
    service: GameroomService = Depends(get_gameroom_service)
) -> GameroomResponse:
    """게임룸을 생성합니다."""
    guest_uuid = request.cookies.get("kkua_guest_uuid")
    if not guest_uuid:
        raise HTTPException(status_code=400, detail="유효한 게스트 UUID가 필요합니다")
    
    return service.create_gameroom(create_data, guest_uuid)

@router.get("/{room_id}", response_model=GameroomDetailResponse)
def get_gameroom(
    room_id: int,
    service: GameroomService = Depends(get_gameroom_service)
) -> GameroomDetailResponse:
    """게임룸 상세 정보를 조회합니다."""
    return service.get_gameroom_detail(room_id)

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
    
    return service.update_gameroom(
        room_id, 
        guest_uuid, 
        update_data.title, 
        update_data.max_players, 
        update_data.game_mode,
        update_data.time_limit
    )

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
    
    return service.delete_gameroom(room_id, guest_uuid)