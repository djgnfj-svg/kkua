"""
Security utilities for token generation and validation
"""

import secrets
import hashlib
import hmac
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt, ExpiredSignatureError
from app_config import settings

logger = logging.getLogger(__name__)


class SecurityUtils:
    """Utility class for security operations"""
    
    @staticmethod
    def generate_secure_token(guest_id: int, nickname: str) -> str:
        """
        Generate a secure session token using HMAC
        """
        # Create payload with timestamp
        timestamp = str(int(datetime.utcnow().timestamp()))
        payload = f"{guest_id}:{nickname}:{timestamp}"
        
        # Create HMAC signature
        signature = hmac.new(
            settings.secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Combine payload and signature
        token = f"{payload}:{signature}"
        
        # Base64 encode for safe transport
        import base64
        return base64.urlsafe_b64encode(token.encode('utf-8')).decode('utf-8')
    
    @staticmethod
    def verify_secure_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a secure session token
        """
        try:
            # Base64 decode
            import base64
            decoded = base64.urlsafe_b64decode(token.encode('utf-8')).decode('utf-8')
            
            # Split token parts
            parts = decoded.split(':')
            if len(parts) != 4:
                return None
            
            guest_id, nickname, timestamp, signature = parts
            
            # Recreate payload
            payload = f"{guest_id}:{nickname}:{timestamp}"
            
            # Verify signature
            expected_signature = hmac.new(
                settings.secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return None
            
            # Check token age (24 hours)
            token_time = datetime.utcfromtimestamp(int(timestamp))
            if datetime.utcnow() - token_time > timedelta(hours=24):
                return None
            
            return {
                'guest_id': int(guest_id),
                'nickname': nickname,
                'created_at': token_time
            }
            
        except ValueError as e:
            logger.warning(f"Token parsing error - invalid format: {e}")
            return None
        except (TypeError, IndexError) as e:
            logger.warning(f"Token structure error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in token validation: {e}", exc_info=True)
            return None
    
    @staticmethod
    def create_jwt_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT token with expiration
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
        return encoded_jwt
    
    @staticmethod
    def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token
        """
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def generate_csrf_token() -> str:
        """
        Generate a CSRF token
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def verify_csrf_token(token: str, expected_token: str) -> bool:
        """
        Verify CSRF token
        """
        return hmac.compare_digest(token, expected_token)