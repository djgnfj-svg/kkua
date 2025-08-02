from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from db.postgres import get_db
from middleware.auth_middleware import get_current_guest
from models.guest_model import Guest
from services.item_service import ItemService
from schemas.item_schema import (
    ItemResponse, ItemInventoryResponse, ItemUseRequest, ItemUseResponse,
    ItemPurchaseRequest, ItemPurchaseResponse, GameItemState
)

router = APIRouter(
    prefix="/items",
    tags=["items"],
)
logger = logging.getLogger(__name__)


def get_item_service(db: Session = Depends(get_db)) -> ItemService:
    """아이템 서비스 의존성"""
    return ItemService(db)


@router.post("/initialize", status_code=status.HTTP_200_OK)
async def initialize_items(
    service: ItemService = Depends(get_item_service)
):
    """기본 아이템들을 데이터베이스에 초기화 (관리자 전용)"""
    try:
        success = service.initialize_default_items()
        if success:
            return {"message": "기본 아이템이 성공적으로 초기화되었습니다"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="아이템 초기화에 실패했습니다"
            )
    except Exception as e:
        logger.error(f"아이템 초기화 API 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="아이템 초기화 중 오류가 발생했습니다"
        )


@router.get("/", response_model=List[ItemResponse])
async def get_all_items(
    service: ItemService = Depends(get_item_service)
):
    """모든 활성 아이템 목록 조회"""
    try:
        items = service.get_all_items()
        return items
    except Exception as e:
        logger.error(f"아이템 목록 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="아이템 목록을 불러오는 중 오류가 발생했습니다"
        )


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item_by_id(
    item_id: int,
    service: ItemService = Depends(get_item_service)
):
    """특정 아이템 정보 조회"""
    try:
        item = service.get_item_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="아이템을 찾을 수 없습니다"
            )
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"아이템 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="아이템 정보를 불러오는 중 오류가 발생했습니다"
        )


@router.get("/inventory/my", response_model=List[ItemInventoryResponse])
async def get_my_inventory(
    guest: Guest = Depends(get_current_guest),
    service: ItemService = Depends(get_item_service)
):
    """내 아이템 인벤토리 조회"""
    try:
        inventory = service.get_player_inventory(guest.guest_id)
        return inventory
    except Exception as e:
        logger.error(f"인벤토리 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="인벤토리를 불러오는 중 오류가 발생했습니다"
        )


@router.post("/purchase", response_model=ItemPurchaseResponse)
async def purchase_item(
    request: ItemPurchaseRequest,
    guest: Guest = Depends(get_current_guest),
    service: ItemService = Depends(get_item_service)
):
    """아이템 구매"""
    try:
        if request.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="구매 수량은 1개 이상이어야 합니다"
            )
        
        result = service.purchase_item(guest.guest_id, request)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"아이템 구매 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="아이템 구매 중 오류가 발생했습니다"
        )


@router.post("/use/{room_id}", response_model=ItemUseResponse)
async def use_item_in_game(
    room_id: int,
    request: ItemUseRequest,
    guest: Guest = Depends(get_current_guest),
    service: ItemService = Depends(get_item_service)
):
    """게임 중 아이템 사용"""
    try:
        logger.info(f"아이템 사용 요청: room_id={room_id}, guest_id={guest.guest_id}, item_id={request.item_id}")
        
        result = service.use_item(room_id, guest.guest_id, request)
        
        if not result.success:
            logger.warning(f"아이템 사용 실패: {result.message}")
        else:
            logger.info(f"아이템 사용 성공: {result.message}")
        
        return result
    except Exception as e:
        logger.error(f"아이템 사용 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="아이템 사용 중 오류가 발생했습니다"
        )


@router.get("/game-state/{room_id}", response_model=GameItemState)
async def get_game_item_state(
    room_id: int,
    guest: Guest = Depends(get_current_guest),
    service: ItemService = Depends(get_item_service)
):
    """게임 중 플레이어의 아이템 상태 조회"""
    try:
        game_state = service.get_game_item_state(room_id, guest.guest_id)
        return game_state
    except Exception as e:
        logger.error(f"게임 아이템 상태 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="게임 아이템 상태를 불러오는 중 오류가 발생했습니다"
        )


@router.delete("/effects/{room_id}", status_code=status.HTTP_200_OK)
async def clear_room_effects(
    room_id: int,
    service: ItemService = Depends(get_item_service)
):
    """방의 모든 아이템 효과 제거 (게임 종료 시)"""
    try:
        service.clear_room_effects(room_id)
        return {"message": f"방 {room_id}의 모든 아이템 효과가 제거되었습니다"}
    except Exception as e:
        logger.error(f"아이템 효과 제거 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="아이템 효과 제거 중 오류가 발생했습니다"
        )