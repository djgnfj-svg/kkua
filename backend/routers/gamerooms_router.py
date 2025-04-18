from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from db.postgres import get_db
from repositories.gameroom_repository import GameroomRepository
from services.gameroom_service import GameroomService
from schemas.gameroom import GameroomResponse

router = APIRouter(
    prefix="/gamerooms",
    tags=["gamerooms"],
)

def get_gameroom_service(db: Session = Depends(get_db)) -> GameroomService:
    repository = GameroomRepository(db)
    return GameroomService(repository, db)

@router.get("/", response_model=List[GameroomResponse], status_code=status.HTTP_200_OK)
def list_gamerooms(service: GameroomService = Depends(get_gameroom_service)):
    return service.list_gamerooms()

@router.post("/", response_model=GameroomResponse, status_code=status.HTTP_201_CREATED)
def create_gameroom(
    request: Request,
    title: str = None,
    max_players: int = None,
    game_mode: str = None,
    time_limit: int = None,
    service: GameroomService = Depends(get_gameroom_service)
):
    return service.create_gameroom(request, title, max_players, game_mode, time_limit)

@router.patch("/{room_id}", response_model=GameroomResponse, status_code=status.HTTP_200_OK)
def update_gameroom(
    room_id: int, 
    request: Request, 
    title: str = None, 
    max_players: int = None, 
    game_mode: str = None, 
    time_limit: int = None, 
    service: GameroomService = Depends(get_gameroom_service)
):
    return service.update_gameroom(room_id, request, title, max_players, game_mode, time_limit)

@router.delete("/{room_id}", status_code=status.HTTP_200_OK)
def delete_gameroom(
    room_id: int, 
    service: GameroomService = Depends(get_gameroom_service)
):
    return service.delete_gameroom(room_id)

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

@router.post("/{room_id}/start", status_code=status.HTTP_200_OK)
def start_game(
    room_id: int, 
    request: Request, 
    service: GameroomService = Depends(get_gameroom_service)
):
    return service.start_game(room_id, request)

@router.post("/{room_id}/end", status_code=status.HTTP_200_OK)
def end_game(
    room_id: int, 
    request: Request, 
    service: GameroomService = Depends(get_gameroom_service)
):
    return service.end_game(room_id, request)

@router.get("/{room_id}/participants", status_code=status.HTTP_200_OK)
def get_gameroom_participants(
    room_id: int, 
    service: GameroomService = Depends(get_gameroom_service)
):
    return service.get_participants(room_id)

@router.get("/check-active-game", status_code=status.HTTP_200_OK)
def check_active_game(
    request: Request, 
    guest_uuid_str: str = None, 
    service: GameroomService = Depends(get_gameroom_service)
):
    return service.check_active_game(request, guest_uuid_str) 