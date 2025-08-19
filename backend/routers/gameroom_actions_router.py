from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session
import logging

from db.postgres import get_db
from middleware.auth_middleware import get_current_guest
from models.guest_model import Guest
from services.gameroom_service import GameroomService
from schemas.gameroom_actions_schema import JoinGameroomResponse

router = APIRouter(
    prefix="/gamerooms",
    tags=["gameroom-actions"],
)
logger = logging.getLogger(__name__)


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
    logger.info(f"방 나가기 API 호출: room_id={room_id}, guest_id={guest.guest_id}")
    try:
        result = service.leave_gameroom(room_id, guest)
        logger.info(f"방 나가기 성공: {result}")
        return result
    except Exception as e:
        logger.error(f"방 나가기 실패: {e}", exc_info=True)
        raise


@router.post("/{room_id}/ready", status_code=status.HTTP_200_OK)
async def toggle_ready_status(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
):
    """참가자의 준비 상태를 토글합니다."""
    logger.info(
        f"준비 상태 토글 API 호출: room_id={room_id}, guest_id={guest.guest_id}"
    )
    try:
        result = await service.toggle_ready_status_with_ws(room_id, guest)
        logger.info(f"준비 상태 토글 성공: {result}")
        return result
    except Exception as e:
        logger.error(f"준비 상태 토글 실패: {e}", exc_info=True)
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
async def end_game(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
):
    """게임을 종료합니다. 방장만 게임을 종료할 수 있습니다."""
    return await service.end_game(room_id, guest)


@router.post("/{room_id}/complete", status_code=status.HTTP_200_OK)
async def complete_game(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
):
    """게임을 완료합니다. 모든 참가자가 완료할 수 있습니다 (테스트용)."""
    return await service.complete_game(room_id, guest)


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


@router.get("/{room_id}/result", status_code=status.HTTP_200_OK)
async def get_game_result(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
):
    """게임 결과를 조회합니다. 게임이 종료된 방의 참가자만 조회할 수 있습니다."""
    logger.info(f"게임 결과 API 호출: room_id={room_id}, guest_id={guest.guest_id}")

    # 실제 게임 결과 데이터 조회
    try:
        result = await service.get_game_result(room_id, guest)
        logger.info(f"실제 게임 결과 반환: room_id={room_id}")
        return result
    except Exception as e:
        logger.error(f"게임 결과 조회 실패: {e}")
        # 에러 발생 시 적절한 HTTP 예외 발생
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404, detail=f"게임 결과를 찾을 수 없습니다: {str(e)}"
        )


@router.get("/{room_id}/test-redis", status_code=status.HTTP_200_OK)
async def test_redis_data(room_id: int):
    """Redis 게임 데이터 테스트용 엔드포인트"""
    try:
        from services.redis_game_service import get_redis_game_service

        redis_game = await get_redis_game_service()

        game_state = await redis_game.get_game_state(room_id)
        all_player_stats = await redis_game.get_all_player_stats(room_id)
        word_entries = await redis_game.get_word_entries(room_id)

        return {
            "game_state": game_state,
            "player_stats": all_player_stats,
            "word_entries": word_entries,
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/{room_id}/is-owner", status_code=status.HTTP_200_OK)
def check_if_owner(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: GameroomService = Depends(get_gameroom_service),
):
    """현재 게스트가 특정 게임룸의 방장인지 확인합니다."""
    return service.check_if_owner(room_id, guest)
