from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.orm import Session

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
    guest_uuid = login_data.guest_uuid or request.cookies.get("kkua_guest_uuid")
    
    nickname = login_data.nickname
    device_info = login_data.device_info or request.headers.get("User-Agent", "")
    
    return service.login(response, guest_uuid, nickname, device_info)
