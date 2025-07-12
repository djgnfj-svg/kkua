"""
CSRF Token Router
"""

from fastapi import APIRouter, Response, Request
from middleware.csrf_middleware import CSRFTokenManager

router = APIRouter(prefix="/csrf", tags=["csrf"])


@router.get("/token")
async def get_csrf_token(request: Request, response: Response):
    """
    Get CSRF token for form submissions
    """
    # Generate and set CSRF token
    csrf_token = CSRFTokenManager.get_csrf_token_for_response(response)
    
    return {
        "csrf_token": csrf_token,
        "message": "CSRF token generated successfully"
    }


@router.get("/status")
async def csrf_status(request: Request):
    """
    Check CSRF protection status
    """
    csrf_token = request.cookies.get("csrf_token")
    session_token = request.cookies.get("session_token")
    
    return {
        "csrf_protection_enabled": True,
        "has_csrf_token": csrf_token is not None,
        "has_session_token": session_token is not None,
        "csrf_token_length": len(csrf_token) if csrf_token else 0
    }