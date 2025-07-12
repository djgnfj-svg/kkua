"""
CSRF Protection Middleware
"""

import secrets
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from utils.security import SecurityUtils
from app_config import settings


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware for FastAPI
    """
    
    def __init__(self, app: ASGIApp, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/ws",  # WebSocket connections
            "/auth/login",  # Login endpoint should be exempted
        ]
        # HTTP methods that require CSRF protection
        self.protected_methods = {"POST", "PUT", "DELETE", "PATCH"}
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and check for CSRF token
        """
        # Skip CSRF check for safe methods and excluded paths
        if (request.method not in self.protected_methods or 
            any(request.url.path.startswith(path) for path in self.exclude_paths)):
            return await call_next(request)
        
        # Get CSRF token from header or form data
        csrf_token = self._get_csrf_token(request)
        
        # Get stored CSRF token from session
        session_token = request.cookies.get("session_token")
        if not session_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token missing: No session found"}
            )
        
        # Get CSRF token from session storage
        stored_csrf_token = request.cookies.get("csrf_token")
        if not stored_csrf_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token missing: No CSRF token in session"}
            )
        
        # Verify CSRF token
        if not csrf_token or not SecurityUtils.verify_csrf_token(csrf_token, stored_csrf_token):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token validation failed"}
            )
        
        # Continue with the request
        return await call_next(request)
    
    def _get_csrf_token(self, request: Request) -> str:
        """
        Extract CSRF token from request headers or form data
        """
        # Check X-CSRF-Token header first
        csrf_token = request.headers.get("X-CSRF-Token")
        if csrf_token:
            return csrf_token
        
        # Check X-CSRFToken header (Django style)
        csrf_token = request.headers.get("X-CSRFToken")
        if csrf_token:
            return csrf_token
        
        # For form submissions, check form data
        # This would need to be implemented if supporting form submissions
        
        return ""


class CSRFTokenManager:
    """
    CSRF Token Management
    """
    
    @staticmethod
    def generate_csrf_token() -> str:
        """
        Generate a new CSRF token
        """
        return SecurityUtils.generate_csrf_token()
    
    @staticmethod
    def set_csrf_cookie(response: Response, csrf_token: str) -> None:
        """
        Set CSRF token in cookie
        """
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=False,  # JavaScript needs to access this
            secure=settings.session_secure,
            samesite=settings.session_samesite,
            max_age=settings.session_timeout
        )
    
    @staticmethod
    def get_csrf_token_for_response(response: Response) -> str:
        """
        Generate CSRF token and set it in response cookie
        """
        csrf_token = CSRFTokenManager.generate_csrf_token()
        CSRFTokenManager.set_csrf_cookie(response, csrf_token)
        return csrf_token