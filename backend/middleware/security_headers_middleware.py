"""
Security Headers Middleware
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app_config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security Headers Middleware for FastAPI
    
    Adds security headers to all responses to protect against common attacks
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """
        Add security headers to response
        """
        response = await call_next(request)
        
        if not settings.enable_security_headers:
            return response
        
        # X-Content-Type-Options: Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options: Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection: Enable XSS filtering
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy: Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content-Security-Policy: Prevent XSS and data injection
        csp_policy = self._get_csp_policy(request)
        response.headers["Content-Security-Policy"] = csp_policy
        
        # Strict-Transport-Security: Enforce HTTPS (only in production)
        if settings.environment == "production" and settings.session_secure:
            response.headers["Strict-Transport-Security"] = f"max-age={settings.hsts_max_age}; includeSubDomains"
        
        # Permissions-Policy: Control feature access
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), "
            "usb=(), screen-wake-lock=(), web-share=()"
        )
        
        # Cross-Origin-Opener-Policy: Prevent cross-origin attacks
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        
        # Cross-Origin-Embedder-Policy: Enable cross-origin isolation
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        
        # Cross-Origin-Resource-Policy: Control resource access
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        return response
    
    def _get_csp_policy(self, request: Request) -> str:
        """
        Generate Content Security Policy based on environment
        """
        if settings.environment == "production":
            # Strict CSP for production
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss:; "
                "font-src 'self' https:; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none'; "
                "upgrade-insecure-requests"
            )
        else:
            # More permissive CSP for development
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' localhost:* 127.0.0.1:*; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https: http:; "
                "connect-src 'self' ws: wss: localhost:* 127.0.0.1:*; "
                "font-src 'self' https:; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )