import logging
import traceback
from typing import Dict, Any
from datetime import datetime
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class StandardErrorResponse:
    """표준화된 에러 응답 생성"""

    @staticmethod
    def create_error_response(
        status_code: int, message: str, details: str = None, error_code: str = None
    ) -> Dict[str, Any]:
        """표준 에러 응답 생성"""
        response = {
            "detail": message,
            "status_code": status_code,
            "success": False,
            "timestamp": str(datetime.utcnow()),
        }

        if details:
            response["details"] = details

        if error_code:
            response["error_code"] = error_code

        return response


class GlobalExceptionHandler(BaseHTTPMiddleware):
    """글로벌 예외 처리 미들웨어"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            return await self.handle_exception(request, exc)

    async def handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """예외 타입별 처리"""

        # HTTPException - FastAPI 표준 예외
        if isinstance(exc, HTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content=StandardErrorResponse.create_error_response(
                    status_code=exc.status_code,
                    message=exc.detail,
                    error_code="HTTP_EXCEPTION",
                ),
            )

        # Pydantic 검증 에러
        elif isinstance(exc, ValidationError):
            logger.warning(f"Validation error on {request.url.path}: {exc}")
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=StandardErrorResponse.create_error_response(
                    status_code=422,
                    message="입력 데이터 검증 실패",
                    details=str(exc),
                    error_code="VALIDATION_ERROR",
                ),
            )

        # 데이터베이스 무결성 에러
        elif isinstance(exc, IntegrityError):
            logger.error(f"Database integrity error on {request.url.path}: {exc}")
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=StandardErrorResponse.create_error_response(
                    status_code=409,
                    message="데이터 무결성 오류가 발생했습니다",
                    error_code="INTEGRITY_ERROR",
                ),
            )

        # 일반 데이터베이스 에러
        elif isinstance(exc, SQLAlchemyError):
            logger.error(f"Database error on {request.url.path}: {exc}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=StandardErrorResponse.create_error_response(
                    status_code=500,
                    message="데이터베이스 오류가 발생했습니다",
                    error_code="DATABASE_ERROR",
                ),
            )

        # 알 수 없는 서버 에러
        else:
            # 상세 에러 로깅
            logger.error(
                f"Unhandled exception on {request.url.path}: {exc}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "client_ip": getattr(request.client, "host", "unknown"),
                    "traceback": traceback.format_exc(),
                },
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=StandardErrorResponse.create_error_response(
                    status_code=500,
                    message="서버 내부 오류가 발생했습니다",
                    error_code="INTERNAL_SERVER_ERROR",
                ),
            )


class ErrorMessages:
    """사용자 친화적 에러 메시지 상수"""

    # 인증 관련
    AUTH_REQUIRED = "로그인이 필요합니다"
    INVALID_CREDENTIALS = "잘못된 인증 정보입니다"
    SESSION_EXPIRED = "세션이 만료되었습니다. 다시 로그인해주세요"
    PERMISSION_DENIED = "권한이 없습니다"

    # 게임방 관련
    ROOM_NOT_FOUND = "게임방을 찾을 수 없습니다"
    ROOM_FULL = "게임방이 가득 찼습니다"
    ALREADY_JOINED = "이미 참가한 게임방입니다"
    NOT_ROOM_OWNER = "방장만 이 작업을 수행할 수 있습니다"
    GAME_IN_PROGRESS = "진행 중인 게임입니다"
    GAME_NOT_STARTED = "아직 게임이 시작되지 않았습니다"

    # 사용자 관련
    USER_NOT_FOUND = "사용자를 찾을 수 없습니다"
    NICKNAME_TAKEN = "이미 사용 중인 닉네임입니다"
    INVALID_NICKNAME = "유효하지 않은 닉네임입니다"

    # 입력 검증 관련
    INVALID_INPUT = "입력 데이터가 올바르지 않습니다"
    MISSING_REQUIRED_FIELD = "필수 입력 항목이 누락되었습니다"

    # 일반 에러
    INTERNAL_ERROR = "서버 내부 오류가 발생했습니다"
    NETWORK_ERROR = "네트워크 오류가 발생했습니다"
    TIMEOUT_ERROR = "요청 시간이 초과되었습니다"

    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "요청 제한을 초과했습니다. 잠시 후 다시 시도해주세요"

    # WebSocket 관련
    WS_CONNECTION_FAILED = "실시간 연결에 실패했습니다"
    WS_MESSAGE_INVALID = "잘못된 메시지 형식입니다"


def create_http_exception(
    status_code: int, message: str, error_code: str = None
) -> HTTPException:
    """사용자 친화적 HTTP 예외 생성"""
    return HTTPException(
        status_code=status_code,
        detail=message,
        headers={"X-Error-Code": error_code} if error_code else None,
    )


# 자주 사용되는 예외들을 미리 정의
class GameRoomExceptions:
    """게임방 관련 예외들"""

    @staticmethod
    def room_not_found():
        return create_http_exception(
            status.HTTP_404_NOT_FOUND, ErrorMessages.ROOM_NOT_FOUND, "ROOM_NOT_FOUND"
        )

    @staticmethod
    def room_full():
        return create_http_exception(
            status.HTTP_400_BAD_REQUEST, ErrorMessages.ROOM_FULL, "ROOM_FULL"
        )

    @staticmethod
    def already_joined():
        return create_http_exception(
            status.HTTP_409_CONFLICT, ErrorMessages.ALREADY_JOINED, "ALREADY_JOINED"
        )

    @staticmethod
    def not_room_owner():
        return create_http_exception(
            status.HTTP_403_FORBIDDEN, ErrorMessages.NOT_ROOM_OWNER, "NOT_ROOM_OWNER"
        )

    @staticmethod
    def game_in_progress():
        return create_http_exception(
            status.HTTP_400_BAD_REQUEST,
            ErrorMessages.GAME_IN_PROGRESS,
            "GAME_IN_PROGRESS",
        )


class AuthExceptions:
    """인증 관련 예외들"""

    @staticmethod
    def auth_required():
        return create_http_exception(
            status.HTTP_401_UNAUTHORIZED, ErrorMessages.AUTH_REQUIRED, "AUTH_REQUIRED"
        )

    @staticmethod
    def invalid_credentials():
        return create_http_exception(
            status.HTTP_401_UNAUTHORIZED,
            ErrorMessages.INVALID_CREDENTIALS,
            "INVALID_CREDENTIALS",
        )

    @staticmethod
    def session_expired():
        return create_http_exception(
            status.HTTP_401_UNAUTHORIZED,
            ErrorMessages.SESSION_EXPIRED,
            "SESSION_EXPIRED",
        )

    @staticmethod
    def permission_denied():
        return create_http_exception(
            status.HTTP_403_FORBIDDEN,
            ErrorMessages.PERMISSION_DENIED,
            "PERMISSION_DENIED",
        )


class UserExceptions:
    """사용자 관련 예외들"""

    @staticmethod
    def user_not_found():
        return create_http_exception(
            status.HTTP_404_NOT_FOUND, ErrorMessages.USER_NOT_FOUND, "USER_NOT_FOUND"
        )

    @staticmethod
    def nickname_taken():
        return create_http_exception(
            status.HTTP_409_CONFLICT, ErrorMessages.NICKNAME_TAKEN, "NICKNAME_TAKEN"
        )

    @staticmethod
    def invalid_nickname():
        return create_http_exception(
            status.HTTP_400_BAD_REQUEST,
            ErrorMessages.INVALID_NICKNAME,
            "INVALID_NICKNAME",
        )
