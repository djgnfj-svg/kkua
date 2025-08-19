"""
Rate limiting middleware for WebSocket and API endpoints
"""

import time
from typing import Dict
from collections import defaultdict, deque
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter using sliding window approach"""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Store request timestamps: {client_id: deque of timestamps}
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())

    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for client"""
        now = time.time()
        client_requests = self.requests[client_id]

        # Remove old requests outside the window
        while client_requests and client_requests[0] <= now - self.window_seconds:
            client_requests.popleft()

        # Check if under limit
        if len(client_requests) < self.max_requests:
            client_requests.append(now)
            return True

        return False

    def get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for client"""
        now = time.time()
        client_requests = self.requests[client_id]

        # Remove old requests
        while client_requests and client_requests[0] <= now - self.window_seconds:
            client_requests.popleft()

        return max(0, self.max_requests - len(client_requests))

    def cleanup_old_entries(self):
        """Cleanup old entries to prevent memory leaks"""
        now = time.time()
        clients_to_remove = []

        for client_id, client_requests in self.requests.items():
            # Remove old timestamps
            while client_requests and client_requests[0] <= now - self.window_seconds:
                client_requests.popleft()

            # If no recent requests, mark for removal
            if not client_requests:
                clients_to_remove.append(client_id)

        for client_id in clients_to_remove:
            del self.requests[client_id]


# Global rate limiters
websocket_rate_limiter = RateLimiter(
    max_requests=30, window_seconds=60
)  # 30 messages per minute
api_rate_limiter = RateLimiter(
    max_requests=100, window_seconds=60
)  # 100 requests per minute


def check_websocket_rate_limit(client_id: str) -> bool:
    """Check WebSocket rate limit for a client"""
    if not websocket_rate_limiter.is_allowed(client_id):
        logger.warning(f"WebSocket rate limit exceeded for client: {client_id}")
        return False
    return True


def check_api_rate_limit(client_id: str) -> bool:
    """Check API rate limit for a client"""
    if not api_rate_limiter.is_allowed(client_id):
        logger.warning(f"API rate limit exceeded for client: {client_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )
    return True


def get_rate_limit_headers(client_id: str) -> Dict[str, str]:
    """Get rate limit headers for HTTP responses"""
    remaining = api_rate_limiter.get_remaining_requests(client_id)
    return {
        "X-RateLimit-Limit": str(api_rate_limiter.max_requests),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Window": str(api_rate_limiter.window_seconds),
    }
