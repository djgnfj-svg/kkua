"""
Session-based authentication service for managing user authentication
"""

from fastapi import HTTPException, status, Response, Request
from typing import Optional, Tuple
import uuid
from repositories.guest_repository import GuestRepository
from models.guest_model import Guest
from services.session_service import get_session_store
from app_config import settings


class AuthService:
    def __init__(self, guest_repo: GuestRepository):
        self.guest_repo = guest_repo
        self.session_store = get_session_store()

    def login(
        self, nickname: Optional[str] = None, device_info: Optional[str] = None
    ) -> Tuple[Guest, str]:
        """
        Login or create a new guest
        Returns: (Guest object, session_token)
        """
        if nickname:
            existing_guest = self.guest_repo.find_by_nickname(nickname)
            if existing_guest:
                guest = self.guest_repo.update_last_login(existing_guest, device_info)
                session_token = self.session_store.create_session(
                    guest.guest_id, guest.nickname
                )
                return guest, session_token
            else:
                guest_uuid_obj = uuid.uuid4()
                guest = self.guest_repo.create(guest_uuid_obj, nickname, device_info)
                session_token = self.session_store.create_session(
                    guest.guest_id, guest.nickname
                )
                return guest, session_token
        else:
            guest_uuid_obj = uuid.uuid4()
            auto_nickname = f"게스트_{str(guest_uuid_obj)[:8]}"
            guest = self.guest_repo.create(guest_uuid_obj, auto_nickname, device_info)
            session_token = self.session_store.create_session(
                guest.guest_id, guest.nickname
            )
            return guest, session_token

    def check_auth_status(self, request: Request) -> dict:
        """
        Check authentication status from session
        """
        session_token = request.cookies.get("session_token")

        if not session_token:
            return {"authenticated": False, "guest": None}

        session_data = self.session_store.get_session(session_token)

        if not session_data:
            return {"authenticated": False, "guest": None}

        guest = self.guest_repo.find_by_id(session_data["guest_id"])

        if guest:
            has_active_game, room_id = self.guest_repo.check_active_game(guest.guest_id)

            return {
                "authenticated": True,
                "guest": {
                    "guest_id": guest.guest_id,
                    "uuid": str(guest.uuid),
                    "nickname": guest.nickname,
                    "created_at": guest.created_at.isoformat()
                    if guest.created_at
                    else None,
                    "last_login": guest.last_login.isoformat()
                    if guest.last_login
                    else None,
                },
                "room_id": room_id if has_active_game else None,
            }
        else:
            self.session_store.delete_session(session_token)
            return {"authenticated": False, "guest": None}

    def logout(self, request: Request, response: Response) -> dict:
        """
        Logout user by clearing session and cookies
        """
        session_token = request.cookies.get("session_token")

        if session_token:
            self.session_store.delete_session(session_token)

        response.delete_cookie("session_token")
        response.delete_cookie("csrf_token")
        return {"message": "로그아웃되었습니다"}

    def update_profile(self, request: Request, nickname: str) -> Guest:
        """
        Update user profile
        """
        session_token = request.cookies.get("session_token")

        if not session_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        session_data = self.session_store.get_session(session_token)

        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session"
            )

        guest = self.guest_repo.find_by_id(session_data["guest_id"])

        if not guest:
            self.session_store.delete_session(session_token)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication",
            )

        existing_guest = self.guest_repo.find_by_nickname(nickname)
        if existing_guest and existing_guest.guest_id != guest.guest_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="닉네임이 이미 사용 중입니다",
            )

        updated_guest = self.guest_repo.update_nickname(guest, nickname)
        self.session_store.update_session(session_token, nickname=nickname)

        return updated_guest

    def set_auth_cookies(self, response: Response, session_token: str) -> None:
        """
        Set authentication cookies with session token and CSRF token
        """
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=settings.session_secure,
            samesite=settings.session_samesite,
            max_age=settings.session_timeout,
        )

        return None  # Simplified: no CSRF token

    def get_session_stats(self) -> dict:
        """
        Get session statistics for admin/debugging
        """
        self.session_store.cleanup_expired_sessions()
        return {
            "active_sessions": self.session_store.get_session_count(),
            "total_guests": len(
                set(
                    session["guest_id"]
                    for session in self.session_store.sessions.values()
                )
            ),
        }
