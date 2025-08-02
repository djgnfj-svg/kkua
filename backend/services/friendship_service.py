from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status
import logging

from repositories.friendship_repository import FriendshipRepository
from repositories.guest_repository import GuestRepository
from models.friendship_model import Friendship, FriendshipStatus
from models.guest_model import Guest
from schemas.friendship_schema import (
    FriendRequestCreate, FriendRequestResponse, FriendsListResponse,
    FriendRequestsResponse, FriendSearchRequest, UserSearchResponse,
    FriendshipStatusResponse, FriendshipStats, FriendInfo, FriendRequestInfo,
    UserSearchResult
)

logger = logging.getLogger(__name__)


class FriendshipService:
    """친구 관계 비즈니스 로직을 처리하는 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.friendship_repo = FriendshipRepository(db)
        self.guest_repo = GuestRepository(db)

    def send_friend_request(self, requester: Guest, request_data: FriendRequestCreate) -> Dict[str, Any]:
        """친구 요청을 보냅니다."""
        target_user_id = request_data.target_user_id
        
        # 대상 사용자 존재 확인
        target_user = self.guest_repo.find_by_id(target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="대상 사용자를 찾을 수 없습니다"
            )
        
        # 친구 요청 가능 여부 확인
        can_send, reason = self.friendship_repo.can_send_friend_request(
            requester.guest_id, target_user_id
        )
        if not can_send:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=reason
            )
        
        try:
            # 친구 요청 생성
            friendship = self.friendship_repo.create_friend_request(
                requester_id=requester.guest_id,
                addressee_id=target_user_id,
                memo=request_data.memo
            )
            
            logger.info(f"친구 요청 전송: {requester.guest_id} -> {target_user_id}")
            
            return {
                "friendship_id": friendship.friendship_id,
                "target_user": {
                    "guest_id": target_user.guest_id,
                    "nickname": target_user.nickname
                },
                "status": friendship.status.value,
                "message": f"{target_user.nickname}님에게 친구 요청을 보냈습니다"
            }
            
        except Exception as e:
            logger.error(f"친구 요청 전송 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="친구 요청 전송에 실패했습니다"
            )

    def respond_to_friend_request(self, user: Guest, friendship_id: int, response: FriendRequestResponse) -> Dict[str, Any]:
        """친구 요청에 응답합니다 (수락/거절)."""
        friendship = self.friendship_repo.find_friendship_by_id(friendship_id)
        
        if not friendship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="친구 요청을 찾을 수 없습니다"
            )
        
        # 요청 받은 사용자인지 확인
        if friendship.addressee_id != user.guest_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 친구 요청에 응답할 권한이 없습니다"
            )
        
        # 요청 상태 확인
        if friendship.status != FriendshipStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 처리된 친구 요청입니다"
            )
        
        try:
            if response.action == "accept":
                updated_friendship = self.friendship_repo.accept_friend_request(
                    friendship_id, user.guest_id
                )
                message = f"{friendship.requester.nickname}님과 친구가 되었습니다"
                
            else:  # reject
                updated_friendship = self.friendship_repo.reject_friend_request(
                    friendship_id, user.guest_id
                )
                message = "친구 요청을 거절했습니다"
            
            if not updated_friendship:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="친구 요청 응답에 실패했습니다"
                )
            
            logger.info(f"친구 요청 응답: {friendship_id} - {response.action}")
            
            return {
                "friendship_id": friendship_id,
                "action": response.action,
                "status": updated_friendship.status.value,
                "message": message
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"친구 요청 응답 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="친구 요청 응답에 실패했습니다"
            )

    def get_friends_list(self, user: Guest, limit: int = 50, offset: int = 0) -> FriendsListResponse:
        """사용자의 친구 목록을 조회합니다."""
        try:
            friends_data, total = self.friendship_repo.get_friends_list(
                user.guest_id, limit, offset
            )
            
            friends = [
                FriendInfo(
                    guest_id=friend['guest_id'],
                    nickname=friend['nickname'],
                    status=friend['status'],
                    friendship_date=friend['friendship_date']
                ) for friend in friends_data
            ]
            
            return FriendsListResponse(
                friends=friends,
                total_count=total,
                online_count=0  # TODO: 실시간 상태 구현 시 업데이트
            )
            
        except Exception as e:
            logger.error(f"친구 목록 조회 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="친구 목록 조회에 실패했습니다"
            )

    def get_friend_requests(self, user: Guest) -> FriendRequestsResponse:
        """친구 요청 목록을 조회합니다."""
        try:
            # 받은 요청
            received_requests = self.friendship_repo.get_received_requests(user.guest_id)
            received_list = [
                FriendRequestInfo(
                    friendship_id=req.friendship_id,
                    requester_id=req.requester_id,
                    requester_nickname=req.requester.nickname,
                    addressee_id=req.addressee_id,
                    addressee_nickname=user.nickname,
                    status=req.status,
                    created_at=req.created_at,
                    updated_at=req.updated_at,
                    memo=req.memo
                ) for req in received_requests
            ]
            
            # 보낸 요청
            sent_requests = self.friendship_repo.get_sent_requests(user.guest_id)
            sent_list = [
                FriendRequestInfo(
                    friendship_id=req.friendship_id,
                    requester_id=req.requester_id,
                    requester_nickname=user.nickname,
                    addressee_id=req.addressee_id,
                    addressee_nickname=req.addressee.nickname,
                    status=req.status,
                    created_at=req.created_at,
                    updated_at=req.updated_at,
                    memo=req.memo
                ) for req in sent_requests
            ]
            
            return FriendRequestsResponse(
                received_requests=received_list,
                sent_requests=sent_list,
                received_count=len(received_list),
                sent_count=len(sent_list)
            )
            
        except Exception as e:
            logger.error(f"친구 요청 목록 조회 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="친구 요청 목록 조회에 실패했습니다"
            )

    def search_users(self, user: Guest, search_request: FriendSearchRequest) -> UserSearchResponse:
        """사용자를 검색합니다."""
        try:
            users_data = self.friendship_repo.search_users_by_nickname(
                search_request.nickname, user.guest_id, search_request.limit
            )
            
            users = [
                UserSearchResult(
                    guest_id=user_data['guest_id'],
                    nickname=user_data['nickname'],
                    friendship_status=user_data['friendship_status'],
                    can_send_request=user_data['can_send_request']
                ) for user_data in users_data
            ]
            
            return UserSearchResponse(
                users=users,
                total_count=len(users),
                query=search_request.nickname
            )
            
        except Exception as e:
            logger.error(f"사용자 검색 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="사용자 검색에 실패했습니다"
            )

    def remove_friend(self, user: Guest, friend_id: int) -> Dict[str, Any]:
        """친구를 삭제합니다."""
        # 친구 존재 확인
        friend = self.guest_repo.find_by_id(friend_id)
        if not friend:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="친구를 찾을 수 없습니다"
            )
        
        # 친구 관계 확인
        if not self.friendship_repo.find_friendship(user.guest_id, friend_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="친구 관계가 아닙니다"
            )
        
        try:
            success = self.friendship_repo.remove_friend(user.guest_id, friend_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="친구 삭제에 실패했습니다"
                )
            
            logger.info(f"친구 삭제: {user.guest_id} -> {friend_id}")
            
            return {
                "friend_id": friend_id,
                "friend_nickname": friend.nickname,
                "message": f"{friend.nickname}님과의 친구 관계를 삭제했습니다"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"친구 삭제 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="친구 삭제에 실패했습니다"
            )

    def block_user(self, user: Guest, target_user_id: int) -> Dict[str, Any]:
        """사용자를 차단합니다."""
        # 대상 사용자 존재 확인
        target_user = self.guest_repo.find_by_id(target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="대상 사용자를 찾을 수 없습니다"
            )
        
        # 자기 자신 차단 방지
        if user.guest_id == target_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="자기 자신을 차단할 수 없습니다"
            )
        
        try:
            friendship = self.friendship_repo.block_user(user.guest_id, target_user_id)
            
            logger.info(f"사용자 차단: {user.guest_id} -> {target_user_id}")
            
            return {
                "blocked_user_id": target_user_id,
                "blocked_user_nickname": target_user.nickname,
                "message": f"{target_user.nickname}님을 차단했습니다"
            }
            
        except Exception as e:
            logger.error(f"사용자 차단 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="사용자 차단에 실패했습니다"
            )

    def unblock_user(self, user: Guest, target_user_id: int) -> Dict[str, Any]:
        """사용자 차단을 해제합니다."""
        # 대상 사용자 존재 확인
        target_user = self.guest_repo.find_by_id(target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="대상 사용자를 찾을 수 없습니다"
            )
        
        try:
            success = self.friendship_repo.unblock_user(user.guest_id, target_user_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="차단 해제에 실패했습니다. 차단 관계가 존재하지 않을 수 있습니다"
                )
            
            logger.info(f"차단 해제: {user.guest_id} -> {target_user_id}")
            
            return {
                "unblocked_user_id": target_user_id,
                "unblocked_user_nickname": target_user.nickname,
                "message": f"{target_user.nickname}님의 차단을 해제했습니다"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"차단 해제 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="차단 해제에 실패했습니다"
            )

    def get_friendship_status(self, user: Guest, target_user_id: int) -> FriendshipStatusResponse:
        """두 사용자 간의 친구 관계 상태를 조회합니다."""
        # 대상 사용자 존재 확인
        target_user = self.guest_repo.find_by_id(target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="대상 사용자를 찾을 수 없습니다"
            )
        
        try:
            friendship = self.friendship_repo.find_friendship(user.guest_id, target_user_id)
            
            are_friends = False
            status_str = "none"
            can_send_request = True
            is_blocked = False
            
            if friendship:
                if friendship.status == FriendshipStatus.ACCEPTED:
                    are_friends = True
                    status_str = "friends"
                    can_send_request = False
                elif friendship.status == FriendshipStatus.PENDING:
                    status_str = "pending"
                    can_send_request = False
                elif friendship.status == FriendshipStatus.BLOCKED:
                    is_blocked = True
                    status_str = "blocked"
                    can_send_request = False
                elif friendship.status == FriendshipStatus.REJECTED:
                    status_str = "rejected"
                    # 거절 후 24시간 확인은 repository에서 처리
                    can_send_request, _ = self.friendship_repo.can_send_friend_request(
                        user.guest_id, target_user_id
                    )
            
            return FriendshipStatusResponse(
                user1_id=user.guest_id,
                user2_id=target_user_id,
                are_friends=are_friends,
                status=status_str,
                can_send_request=can_send_request,
                is_blocked=is_blocked
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"친구 관계 상태 조회 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="친구 관계 상태 조회에 실패했습니다"
            )

    def get_friendship_stats(self, user: Guest) -> FriendshipStats:
        """사용자의 친구 관계 통계를 조회합니다."""
        try:
            stats_data = self.friendship_repo.get_friendship_stats(user.guest_id)
            
            return FriendshipStats(
                total_friends=stats_data['total_friends'],
                pending_received=stats_data['pending_received'],
                pending_sent=stats_data['pending_sent'],
                friends_online=stats_data['friends_online'],
                recently_active=stats_data['recently_active']
            )
            
        except Exception as e:
            logger.error(f"친구 관계 통계 조회 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="친구 관계 통계 조회에 실패했습니다"
            )