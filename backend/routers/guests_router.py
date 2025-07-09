from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.orm import Session
from config.cookie import GUEST_AUTH_COOKIE, GUEST_UUID_COOKIE

from db.postgres import get_db
from repositories.guest_repository import GuestRepository
from services.guest_service import GuestService
from schemas.guest_schema import GuestResponse, GuestLoginRequest

router = APIRouter(prefix="/guests", tags=["guests"])


def get_guest_service(db: Session = Depends(get_db)) -> GuestService:
    repository = GuestRepository(db)
    return GuestService(repository)


@router.post("/login", response_model=GuestResponse)
def guest_login(
    request: Request,
    response: Response,
    login_data: GuestLoginRequest,
    service: GuestService = Depends(get_guest_service),
) -> GuestResponse:
    # 두 쿠키 중 하나 가져오기 (auth가 우선)
    guest_uuid = request.cookies.get(GUEST_AUTH_COOKIE) or request.cookies.get(
        GUEST_UUID_COOKIE
    )
    nickname = login_data.nickname
    device_info = login_data.device_info or request.headers.get("User-Agent", "")

    return service.login(response, guest_uuid, nickname, device_info)
