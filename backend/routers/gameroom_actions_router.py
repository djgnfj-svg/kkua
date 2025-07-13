from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session

from db.postgres import get_db
from middleware.auth_middleware import get_current_guest
from models.guest_model import Guest
from services.gameroom_service import GameroomService
from schemas.gameroom_actions_schema import JoinGameroomResponse
from schemas.gameroom_schema import GameResultResponse

router = APIRouter(
    prefix="/gamerooms",
    tags=["gameroom-actions"],
)


def get_gameroom_service(
    db: Session = Depends(get_db),
) -> GameroomService:
    return GameroomService(db)


@router.post("/{room_id}/join", response_model=JoinGameroomResponse)
async def join_gameroom(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
):
    """게임룸에 참가합니다."""
    return await service.join_gameroom(room_id, guest)


@router.post("/{room_id}/leave", status_code=status.HTTP_200_OK)
def leave_gameroom(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
):
    """게임룸에서 나갑니다."""
    print(f"🚪 방 나가기 API 호출: room_id={room_id}, guest_id={guest.guest_id}")
    try:
        result = service.leave_gameroom(room_id, guest)
        print(f"✅ 방 나가기 성공: {result}")
        return result
    except Exception as e:
        print(f"❌ 방 나가기 실패: {e}")
        import traceback
        traceback.print_exc()
        raise


@router.post("/{room_id}/ready", status_code=status.HTTP_200_OK)
async def toggle_ready_status(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
):
    """참가자의 준비 상태를 토글합니다."""
    print(f"🔄 준비 상태 토글 API 호출: room_id={room_id}, guest_id={guest.guest_id}")
    try:
        result = await service.toggle_ready_status_with_ws(room_id, guest)
        print(f"✅ 준비 상태 토글 성공: {result}")
        return result
    except Exception as e:
        print(f"❌ 준비 상태 토글 실패: {e}")
        import traceback
        traceback.print_exc()
        raise


@router.post("/{room_id}/start", status_code=status.HTTP_200_OK)
async def start_game(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
):
    """게임을 시작합니다. 방장만 게임을 시작할 수 있습니다."""
    return await service.start_game(room_id, guest)


@router.post("/{room_id}/end", status_code=status.HTTP_200_OK)
def end_game(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
):
    """게임을 종료합니다. 방장만 게임을 종료할 수 있습니다."""
    return service.end_game(room_id, guest)


@router.get("/{room_id}/participants", status_code=status.HTTP_200_OK)
def get_gameroom_participants(
    room_id: int,
    service: GameroomService = Depends(get_gameroom_service),
):
    """게임룸의 참가자 목록을 조회합니다."""
    return service.get_participants(room_id)


@router.get("/check-active-game", status_code=status.HTTP_200_OK)
def check_active_game(
    guest_uuid_str: str = None,
    service: GameroomService = Depends(get_gameroom_service),
):
    """유저가 현재 참여 중인 게임이 있는지 확인합니다."""
    return service.check_active_game(guest_uuid_str)


@router.get("/{room_id}/result", response_model=GameResultResponse, status_code=status.HTTP_200_OK)
def get_game_result(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
):
    """게임 결과를 조회합니다. 게임이 종료된 방의 참가자만 조회할 수 있습니다."""
    return service.get_game_result(room_id, guest)


@router.get("/{room_id}/is-owner", status_code=status.HTTP_200_OK)
def check_if_owner(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
):
    """현재 게스트가 특정 게임룸의 방장인지 확인합니다."""
    return service.check_if_owner(room_id, guest)
