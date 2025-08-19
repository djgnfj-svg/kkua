"""
Request Logging Middleware
"""

import time
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from config.logging_config import log_performance, log_audit, log_security


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Request logging middleware that adds request context and logs request/response
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next):
        """
        Process request and add logging context
        """
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]

        # Get user context
        session_token = request.cookies.get("session_token", "anonymous")
        user_id = "anonymous"

        # Add context to request state
        request.state.request_id = request_id
        request.state.user_id = user_id
        request.state.session_id = (
            session_token[:8] if session_token != "anonymous" else "anonymous"
        )

        # Start timing
        start_time = time.time()

        # Log request start
        self.logger.info(
            f"REQUEST START: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "session_id": request.state.session_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("User-Agent", "Unknown"),
            },
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            self.logger.info(
                f"REQUEST END: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "session_id": request.state.session_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": duration,
                    "response_size": response.headers.get("Content-Length", "unknown"),
                },
            )

            # Log performance metrics for slow requests
            if duration > 1.0:  # Log requests taking more than 1 second
                log_performance(
                    f"{request.method} {request.url.path}",
                    duration,
                    {
                        "request_id": request_id,
                        "user_id": user_id,
                        "session_id": request.state.session_id,
                        "status_code": response.status_code,
                    },
                )

            # Log audit events for important actions
            if self._should_audit(request, response):
                log_audit(
                    f"{request.method} {request.url.path}",
                    user_id,
                    {
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "client_ip": self._get_client_ip(request),
                    },
                )

            # Log security events
            if self._is_security_event(request, response):
                log_security(
                    f"Security event: {request.method} {request.url.path} - {response.status_code}",
                    {
                        "request_id": request_id,
                        "user_id": user_id,
                        "client_ip": self._get_client_ip(request),
                        "user_agent": request.headers.get("User-Agent", "Unknown"),
                    },
                )

            return response

        except Exception as e:
            # Calculate duration for error case
            duration = time.time() - start_time

            # Log error
            self.logger.error(
                f"REQUEST ERROR: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "session_id": request.state.session_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration": duration,
                },
                exc_info=True,
            )

            # Log security event for errors
            log_security(
                f"Request error: {request.method} {request.url.path} - {str(e)}",
                {
                    "request_id": request_id,
                    "user_id": user_id,
                    "client_ip": self._get_client_ip(request),
                    "error": str(e),
                },
            )

            raise

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address
        """
        # Check for forwarded headers first (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to client host
        return request.client.host if request.client else "unknown"

    def _should_audit(self, request: Request, response: Response) -> bool:
        """
        Determine if request should be audited
        """
        # Audit authentication actions
        if request.url.path.startswith("/auth/"):
            return True

        # Audit game room actions
        if request.url.path.startswith("/gamerooms/") and request.method in [
            "POST",
            "PUT",
            "DELETE",
        ]:
            return True

        # Audit admin actions
        if request.url.path.startswith("/admin/"):
            return True

        return False

    def _is_security_event(self, request: Request, response: Response) -> bool:
        """
        Determine if this is a security-related event
        """
        # Log failed authentication attempts
        if request.url.path.startswith("/auth/") and response.status_code >= 400:
            return True

        # Log CSRF failures
        if response.status_code == 403:
            return True

        # Log rate limiting
        if response.status_code == 429:
            return True

        # Log suspicious activity (multiple 4xx errors)
        if response.status_code >= 400 and response.status_code < 500:
            return True

        return False
