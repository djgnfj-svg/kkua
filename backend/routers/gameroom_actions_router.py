from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from typing import Dict, Any

from db.postgres import get_db
from repositories.gameroom_repository import GameroomRepository
from repositories.guest_repository import GuestRepository
from services.gameroom_actions_service import GameroomActionsService
from schemas.gameroom_schema import JoinGameroomResponse

router = APIRouter(
    prefix="/gamerooms",
    tags=["gameroom-actions"],
)

def get_gameroom_actions_service(db: Session = Depends(get_db)) -> GameroomActionsService:
    gameroom_repo = GameroomRepository(db)
    guest_repo = GuestRepository(db)
    return GameroomActionsService(gameroom_repo, guest_repo)

@router.post("/{room_id}/join", response_model=JoinGameroomResponse)
def join_gameroom(
    room_id: int, 
    request: Request, 
    service: GameroomActionsService = Depends(get_gameroom_actions_service)
):
    """게임룸에 참가합니다."""
    return service.join_gameroom(room_id, request)

@router.post("/{room_id}/leave", status_code=status.HTTP_200_OK)
def leave_gameroom(
    room_id: int, 
    request: Request, 
    service: GameroomActionsService = Depends(get_gameroom_actions_service)
):
    """게임룸에서 나갑니다."""
    return service.leave_gameroom(room_id, request)

@router.post("/{room_id}/start", status_code=status.HTTP_200_OK)
def start_game(
    room_id: int, 
    request: Request, 
    service: GameroomActionsService = Depends(get_gameroom_actions_service)
):
    """게임을 시작합니다. 방장만 게임을 시작할 수 있습니다."""
    return service.start_game(room_id, request)

@router.post("/{room_id}/end", status_code=status.HTTP_200_OK)
def end_game(
    room_id: int, 
    request: Request, 
    service: GameroomActionsService = Depends(get_gameroom_actions_service)
):
    """게임을 종료합니다. 방장만 게임을 종료할 수 있습니다."""
    return service.end_game(room_id, request)

@router.get("/{room_id}/participants", status_code=status.HTTP_200_OK)
def get_gameroom_participants(
    room_id: int, 
    service: GameroomActionsService = Depends(get_gameroom_actions_service)
):
    """게임룸의 참가자 목록을 조회합니다."""
    return service.get_participants(room_id)

@router.get("/check-active-game", status_code=status.HTTP_200_OK)
def check_active_game(
    request: Request, 
    guest_uuid_str: str = None, 
    service: GameroomActionsService = Depends(get_gameroom_actions_service)
):
    """유저가 현재 참여 중인 게임이 있는지 확인합니다."""
    return service.check_active_game(request, guest_uuid_str)

@router.get("/{room_id}/is-owner", status_code=status.HTTP_200_OK)
def check_if_owner(
    room_id: int,
    request: Request,
    service: GameroomActionsService = Depends(get_gameroom_actions_service)
):
    """현재 게스트가 특정 게임룸의 방장인지 확인합니다."""
    return service.check_if_owner(room_id, request) 