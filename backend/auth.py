"""
JWT 토큰 기반 인증 시스템
WebSocket 연결 시 사용자 인증을 위한 JWT 토큰 처리
"""

import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# 환경 변수에서 비밀 키 가져오기
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24  # 24시간으로 고정

# 비밀번호 해싱 (게스트 계정이지만 향후 확장 대비)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class AuthenticationError(Exception):
    """인증 관련 오류"""
    pass


class TokenManager:
    """JWT 토큰 관리 클래스"""
    
    def __init__(self):
        self.secret_key = JWT_SECRET
        self.algorithm = ALGORITHM
        self.expire_hours = ACCESS_TOKEN_EXPIRE_HOURS
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """JWT 액세스 토큰 생성"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=self.expire_hours)
        
        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.info(f"JWT 토큰 생성 완료: user_id={data.get('user_id')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"JWT 토큰 생성 실패: {e}")
            raise AuthenticationError("토큰 생성에 실패했습니다")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """JWT 토큰 검증"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 만료 시간 확인
            exp = payload.get("exp")
            if exp and datetime.now(timezone.utc) > datetime.fromtimestamp(exp, tz=timezone.utc):
                raise AuthenticationError("토큰이 만료되었습니다")
            
            logger.debug(f"JWT 토큰 검증 성공: user_id={payload.get('user_id')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("만료된 JWT 토큰")
            raise AuthenticationError("토큰이 만료되었습니다")
        except jwt.JWTError as e:
            logger.error(f"JWT 토큰 검증 실패: {e}")
            raise AuthenticationError("유효하지 않은 토큰입니다")
    
    def extract_user_info(self, token: str) -> Dict[str, Any]:
        """토큰에서 사용자 정보 추출"""
        payload = self.verify_token(token)
        
        return {
            "user_id": payload.get("user_id"),
            "nickname": payload.get("nickname"),
            "exp": payload.get("exp"),
            "iat": payload.get("iat")
        }


class AuthService:
    """인증 서비스 클래스"""
    
    def __init__(self):
        self.token_manager = TokenManager()
    
    def create_guest_token(self, user_id: int, nickname: str) -> str:
        """게스트 사용자용 토큰 생성"""
        token_data = {
            "user_id": user_id,
            "nickname": nickname,
            "user_type": "guest",
            "permissions": ["game_play", "chat"]
        }
        
        return self.token_manager.create_access_token(token_data)
    
    def authenticate_websocket(self, token: str) -> Dict[str, Any]:
        """WebSocket 연결 시 토큰 인증"""
        try:
            user_info = self.token_manager.extract_user_info(token)
            
            # 기본 검증
            if not user_info.get("user_id") or not user_info.get("nickname"):
                raise AuthenticationError("토큰에 필수 정보가 없습니다")
            
            return user_info
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"WebSocket 인증 중 오류: {e}")
            raise AuthenticationError("인증 처리 중 오류가 발생했습니다")
    
    def validate_game_permission(self, user_info: Dict[str, Any], action: str) -> bool:
        """게임 액션 권한 확인"""
        permissions = user_info.get("permissions", [])
        
        # 기본 게임 권한 확인
        if action in ["join_game", "submit_word", "use_item"] and "game_play" not in permissions:
            return False
        
        # 채팅 권한 확인
        if action == "chat" and "chat" not in permissions:
            return False
        
        return True
    
    def refresh_token(self, old_token: str) -> str:
        """토큰 갱신"""
        try:
            payload = self.token_manager.verify_token(old_token)
            
            # 새 토큰 생성 (기존 정보 유지)
            new_token_data = {
                "user_id": payload.get("user_id"),
                "nickname": payload.get("nickname"),
                "user_type": payload.get("user_type", "guest"),
                "permissions": payload.get("permissions", ["game_play", "chat"])
            }
            
            return self.token_manager.create_access_token(new_token_data)
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"토큰 갱신 중 오류: {e}")
            raise AuthenticationError("토큰 갱신에 실패했습니다")


def hash_password(password: str) -> str:
    """비밀번호 해시화 (향후 사용자 계정 확장시 사용)"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증 (향후 사용자 계정 확장시 사용)"""
    return pwd_context.verify(plain_password, hashed_password)


def extract_token_from_websocket_headers(headers: Dict[str, str]) -> Optional[str]:
    """WebSocket 헤더에서 토큰 추출"""
    # Authorization 헤더에서 Bearer 토큰 추출
    auth_header = headers.get("authorization") or headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    
    # Cookie에서 토큰 추출 (대안 방법)
    cookie_header = headers.get("cookie") or headers.get("Cookie")
    if cookie_header:
        cookies = dict(item.split("=", 1) for item in cookie_header.split("; ") if "=" in item)
        return cookies.get("access_token")
    
    return None


# 전역 인증 서비스 인스턴스
auth_service = AuthService()


def get_current_user_from_token(token: str) -> Dict[str, Any]:
    """토큰에서 현재 사용자 정보 가져오기"""
    try:
        return auth_service.authenticate_websocket(token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def websocket_auth_dependency(websocket_headers: Dict[str, str]) -> Dict[str, Any]:
    """WebSocket 연결용 인증 의존성"""
    token = extract_token_from_websocket_headers(websocket_headers)
    
    if not token:
        raise AuthenticationError("인증 토큰이 필요합니다")
    
    return get_current_user_from_token(token)