"""
게임 모드 관련 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from db.postgres import get_db
from models.guest_model import Guest
from middleware.auth_middleware import get_current_guest, require_admin
from services.game_mode_service import GameModeService
from schemas.game_mode_schema import (
    GameModeResponse, GameModeListResponse, GameModeCreate, GameModeUpdate,
    GameRoomModeRequest, GameModeValidationResponse
)
import logging

router = APIRouter(prefix="/game-modes", tags=["game-modes"])
logger = logging.getLogger(__name__)


def get_game_mode_service(db: Session = Depends(get_db)) -> GameModeService:
    """게임 모드 서비스 의존성"""
    return GameModeService(db)


@router.post("/initialize", status_code=status.HTTP_200_OK)
async def initialize_game_modes(
    service: GameModeService = Depends(get_game_mode_service)
):
    """기본 게임 모드 초기화 (관리자 전용)"""
    try:
        success = service.initialize_default_modes()
        
        if success:
            return {"message": "기본 게임 모드가 성공적으로 초기화되었습니다"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="게임 모드 초기화에 실패했습니다"
            )
            
    except Exception as e:
        logger.error(f"게임 모드 초기화 API 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="게임 모드 초기화 중 오류가 발생했습니다"
        )


@router.get("/", response_model=GameModeListResponse)
async def get_all_game_modes(
    active_only: bool = True,
    service: GameModeService = Depends(get_game_mode_service)
):
    """모든 게임 모드 조회"""
    try:
        modes = service.get_all_modes(active_only=active_only)
        active_count = len([m for m in modes if m.is_active])
        
        return GameModeListResponse(
            modes=modes,
            total=len(modes),
            active_count=active_count
        )
        
    except Exception as e:
        logger.error(f"게임 모드 목록 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="게임 모드 목록을 불러오는 중 오류가 발생했습니다"
        )


@router.get("/default", response_model=GameModeResponse)
async def get_default_game_mode(
    service: GameModeService = Depends(get_game_mode_service)
):
    """기본 게임 모드 조회"""
    try:
        mode = service.get_default_mode()
        
        if not mode:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="기본 게임 모드를 찾을 수 없습니다"
            )
        
        return mode
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기본 게임 모드 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="기본 게임 모드 조회 중 오류가 발생했습니다"
        )


@router.get("/{mode_name}", response_model=GameModeResponse)
async def get_game_mode_by_name(
    mode_name: str,
    service: GameModeService = Depends(get_game_mode_service)
):
    """이름으로 게임 모드 조회"""
    try:
        mode = service.get_mode_by_name(mode_name)
        
        if not mode:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"게임 모드를 찾을 수 없습니다: {mode_name}"
            )
        
        return mode
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"게임 모드 조회 오류 (name: {mode_name}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="게임 모드 조회 중 오류가 발생했습니다"
        )


@router.post("/validate", response_model=GameModeValidationResponse)
async def validate_game_mode_for_room(
    request: GameRoomModeRequest,
    service: GameModeService = Depends(get_game_mode_service)
):
    """게임방에서 사용할 모드 설정 검증"""
    try:
        validation_result = service.validate_mode_for_room(request)
        return validation_result
        
    except Exception as e:
        logger.error(f"게임 모드 검증 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="게임 모드 검증 중 오류가 발생했습니다"
        )


@router.post("/", response_model=GameModeResponse, status_code=status.HTTP_201_CREATED)
async def create_game_mode(
    mode_data: GameModeCreate,
    admin_user: Guest = Depends(require_admin),
    service: GameModeService = Depends(get_game_mode_service)
):
    """새 게임 모드 생성 (관리자 전용)"""
    try:
        
        mode = service.create_mode(mode_data)
        
        if not mode:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="게임 모드 생성에 실패했습니다. 이름이 중복되었을 수 있습니다."
            )
        
        return mode
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"게임 모드 생성 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="게임 모드 생성 중 오류가 발생했습니다"
        )


@router.put("/{mode_id}", response_model=GameModeResponse)
async def update_game_mode(
    mode_id: int,
    mode_data: GameModeUpdate,
    admin_user: Guest = Depends(require_admin),
    service: GameModeService = Depends(get_game_mode_service)
):
    """게임 모드 업데이트 (관리자 전용)"""
    try:
        
        mode = service.update_mode(mode_id, mode_data)
        
        if not mode:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"게임 모드를 찾을 수 없습니다: {mode_id}"
            )
        
        return mode
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"게임 모드 업데이트 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="게임 모드 업데이트 중 오류가 발생했습니다"
        )


@router.get("/statistics/overview")
async def get_game_mode_statistics(
    service: GameModeService = Depends(get_game_mode_service)
) -> Dict[str, Any]:
    """게임 모드 통계 조회"""
    try:
        stats = service.get_mode_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"게임 모드 통계 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="게임 모드 통계 조회 중 오류가 발생했습니다"
        )