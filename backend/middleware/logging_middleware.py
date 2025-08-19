"""
Simple Request Logging Middleware
"""

import time
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Simple request logging middleware"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next):
        """Process request and log"""
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # Log request
        self.logger.info(f"[{request_id}] {request.method} {request.url.path}")

        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log response
            self.logger.info(
                f"[{request_id}] {response.status_code} - {duration:.3f}s"
            )
            
            return response

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"[{request_id}] ERROR: {str(e)} - {duration:.3f}s"
            )
            raise