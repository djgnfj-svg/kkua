from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from db.postgres import get_db
from services.friendship_service import FriendshipService
from middleware.auth_middleware import get_current_guest, require_admin
from models.guest_model import Guest
from schemas.friendship_schema import (
    FriendRequestCreate, FriendRequestResponse, FriendsListResponse,
    FriendRequestsResponse, FriendSearchRequest, UserSearchResponse,
    FriendshipStatusResponse, FriendshipStats
)

router = APIRouter(
    prefix="/friends",
    tags=["friendship"],
)


def get_friendship_service(db: Session = Depends(get_db)) -> FriendshipService:
    return FriendshipService(db)


@router.post("/request", status_code=status.HTTP_201_CREATED)
def send_friend_request(
    request_data: FriendRequestCreate,
    current_user: Guest = Depends(get_current_guest),
    service: FriendshipService = Depends(get_friendship_service),
) -> Dict[str, Any]:
    """친구 요청을 보냅니다."""
    return service.send_friend_request(current_user, request_data)


@router.post("/request/{friendship_id}/respond")
def respond_to_friend_request(
    friendship_id: int,
    response: FriendRequestResponse,
    current_user: Guest = Depends(get_current_guest),
    service: FriendshipService = Depends(get_friendship_service),
) -> Dict[str, Any]:
    """친구 요청에 응답합니다 (수락/거절)."""
    return service.respond_to_friend_request(current_user, friendship_id, response)


@router.get("/", response_model=FriendsListResponse)
def get_friends_list(
    limit: int = Query(default=50, ge=1, le=100, description="조회할 친구 수"),
    offset: int = Query(default=0, ge=0, description="건너뛸 친구 수"),
    current_user: Guest = Depends(get_current_guest),
    service: FriendshipService = Depends(get_friendship_service),
) -> FriendsListResponse:
    """친구 목록을 조회합니다."""
    return service.get_friends_list(current_user, limit, offset)


@router.get("/requests", response_model=FriendRequestsResponse)
def get_friend_requests(
    current_user: Guest = Depends(get_current_guest),
    service: FriendshipService = Depends(get_friendship_service),
) -> FriendRequestsResponse:
    """친구 요청 목록을 조회합니다 (받은 요청과 보낸 요청)."""
    return service.get_friend_requests(current_user)


@router.post("/search", response_model=UserSearchResponse)
def search_users(
    search_request: FriendSearchRequest,
    current_user: Guest = Depends(get_current_guest),
    service: FriendshipService = Depends(get_friendship_service),
) -> UserSearchResponse:
    """닉네임으로 사용자를 검색합니다."""
    return service.search_users(current_user, search_request)


@router.delete("/{friend_id}")
def remove_friend(
    friend_id: int,
    current_user: Guest = Depends(get_current_guest),
    service: FriendshipService = Depends(get_friendship_service),
) -> Dict[str, Any]:
    """친구를 삭제합니다."""
    return service.remove_friend(current_user, friend_id)


@router.post("/block/{target_user_id}")
def block_user(
    target_user_id: int,
    current_user: Guest = Depends(get_current_guest),
    service: FriendshipService = Depends(get_friendship_service),
) -> Dict[str, Any]:
    """사용자를 차단합니다."""
    return service.block_user(current_user, target_user_id)


@router.delete("/block/{target_user_id}")
def unblock_user(
    target_user_id: int,
    current_user: Guest = Depends(get_current_guest),
    service: FriendshipService = Depends(get_friendship_service),
) -> Dict[str, Any]:
    """사용자 차단을 해제합니다."""
    return service.unblock_user(current_user, target_user_id)


@router.get("/status/{target_user_id}", response_model=FriendshipStatusResponse)
def get_friendship_status(
    target_user_id: int,
    current_user: Guest = Depends(get_current_guest),
    service: FriendshipService = Depends(get_friendship_service),
) -> FriendshipStatusResponse:
    """두 사용자 간의 친구 관계 상태를 조회합니다."""
    return service.get_friendship_status(current_user, target_user_id)


@router.get("/stats", response_model=FriendshipStats)
def get_friendship_stats(
    current_user: Guest = Depends(get_current_guest),
    service: FriendshipService = Depends(get_friendship_service),
) -> FriendshipStats:
    """사용자의 친구 관계 통계를 조회합니다."""
    return service.get_friendship_stats(current_user)


# 관리자용 엔드포인트 (향후 확장)
@router.get("/admin/statistics")
def get_friendship_admin_stats(
    admin_user: Guest = Depends(require_admin),
    service: FriendshipService = Depends(get_friendship_service),
) -> Dict[str, Any]:
    """전체 친구 시스템 통계를 조회합니다. (관리자 전용)"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="관리자 통계는 아직 구현되지 않았습니다"
    )