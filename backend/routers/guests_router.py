from fastapi import APIRouter, Depends, Response, Request, Cookie
from sqlalchemy.orm import Session
from typing import Optional

from db.postgres import get_db
from repositories.guest_repository import GuestRepository
from services.guest_service import GuestService
from schemas.guest_schema import GuestResponse, GuestLoginRequest

router = APIRouter(
    prefix="/guests",
    tags=["guests"]
)

def get_guest_service(db: Session = Depends(get_db)) -> GuestService:
    repository = GuestRepository(db)
    return GuestService(repository)

@router.post("/login", response_model=GuestResponse)
def guest_login(
    request: Request,
    response: Response,
    login_data: GuestLoginRequest,
    service: GuestService = Depends(get_guest_service)
) -> GuestResponse:
    # 두 쿠키 모두 확인 (auth가 우선)
    guest_uuid = request.cookies.get("kkua_guest_auth") or request.cookies.get("kkua_guest_uuid")
    nickname = login_data.nickname
    device_info = login_data.device_info or request.headers.get("User-Agent", "")
    
    return service.login(response, guest_uuid, nickname, device_info)
