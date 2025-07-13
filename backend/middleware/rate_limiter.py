import time
from collections import defaultdict, deque
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate Limiting 구현 클래스"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # IP별 요청 기록: ip -> deque of timestamps
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())
    
    def is_allowed(self, client_ip: str) -> Tuple[bool, Optional[int]]:
        """요청이 허용되는지 확인
        
        Returns:
            Tuple[bool, Optional[int]]: (허용 여부, 리셋까지 남은 시간)
        """
        now = time.time()
        client_requests = self.requests[client_ip]
        
        # 윈도우 밖의 오래된 요청들 제거
        while client_requests and client_requests[0] <= now - self.window_seconds:
            client_requests.popleft()
        
        # 현재 요청 수 확인
        if len(client_requests) >= self.max_requests:
            # 가장 오래된 요청이 언제 만료되는지 계산
            oldest_request = client_requests[0]
            reset_time = int(oldest_request + self.window_seconds - now)
            return False, reset_time
        
        # 요청 허용
        client_requests.append(now)
        return True, None
    
    def get_remaining_requests(self, client_ip: str) -> int:
        """남은 요청 수 반환"""
        now = time.time()
        client_requests = self.requests[client_ip]
        
        # 윈도우 밖의 요청들 제거
        while client_requests and client_requests[0] <= now - self.window_seconds:
            client_requests.popleft()
        
        return max(0, self.max_requests - len(client_requests))


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate Limiting 미들웨어"""
    
    def __init__(self, app, rate_limiters: Dict[str, RateLimiter] = None):
        super().__init__(app)
        
        # 기본 Rate Limiter 설정 (개발 환경에서는 더 관대하게)
        if rate_limiters is None:
            rate_limiters = {
                "default": RateLimiter(max_requests=1000, window_seconds=60),  # 기본: 1분에 1000개
                "auth": RateLimiter(max_requests=100, window_seconds=60),      # 인증: 1분에 100개
                "websocket": RateLimiter(max_requests=300, window_seconds=60), # WebSocket: 1분에 300개
            }
        
        self.rate_limiters = rate_limiters
        
        # 경로별 Rate Limiter 매핑
        self.path_limiter_map = {
            "/auth/login": "auth",
            "/auth/logout": "auth",
            "/ws/": "websocket",
        }
    
    def get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 주소 추출"""
        # X-Forwarded-For 헤더 확인 (프록시 뒤에 있는 경우)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # X-Real-IP 헤더 확인
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 기본적으로 client host 사용
        return request.client.host if request.client else "unknown"
    
    def get_rate_limiter(self, path: str) -> RateLimiter:
        """경로에 해당하는 Rate Limiter 반환"""
        for pattern, limiter_name in self.path_limiter_map.items():
            if path.startswith(pattern):
                return self.rate_limiters[limiter_name]
        
        return self.rate_limiters["default"]
    
    async def dispatch(self, request: Request, call_next):
        # Rate Limiting 제외 경로
        excluded_paths = ["/health", "/docs", "/redoc", "/openapi.json", "/static"]
        
        if any(request.url.path.startswith(path) for path in excluded_paths):
            return await call_next(request)
        
        client_ip = self.get_client_ip(request)
        rate_limiter = self.get_rate_limiter(request.url.path)
        
        # Rate Limiting 검사
        is_allowed, reset_time = rate_limiter.is_allowed(client_ip)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for IP {client_ip} on path {request.url.path}")
            
            # Rate Limit 초과 응답
            headers = {
                "X-RateLimit-Limit": str(rate_limiter.max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time) if reset_time else "60",
                "Retry-After": str(reset_time) if reset_time else "60"
            }
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Try again in {reset_time} seconds.",
                    "status_code": 429
                },
                headers=headers
            )
        
        # 요청 처리
        response = await call_next(request)
        
        # Rate Limit 헤더 추가
        remaining = rate_limiter.get_remaining_requests(client_ip)
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(rate_limiter.window_seconds)
        
        return response


class WebSocketRateLimiter:
    """WebSocket 전용 Rate Limiter"""
    
    def __init__(self, max_messages: int = 30, window_seconds: int = 60):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        # 사용자별 메시지 기록: guest_id -> deque of timestamps
        self.user_messages: Dict[int, deque] = defaultdict(lambda: deque())
    
    def is_message_allowed(self, guest_id: int) -> bool:
        """메시지 전송이 허용되는지 확인"""
        now = time.time()
        user_msgs = self.user_messages[guest_id]
        
        # 윈도우 밖의 오래된 메시지들 제거
        while user_msgs and user_msgs[0] <= now - self.window_seconds:
            user_msgs.popleft()
        
        # 현재 메시지 수 확인
        if len(user_msgs) >= self.max_messages:
            logger.warning(f"Message rate limit exceeded for user {guest_id}")
            return False
        
        # 메시지 허용
        user_msgs.append(now)
        return True
    
    def get_remaining_messages(self, guest_id: int) -> int:
        """남은 메시지 수 반환"""
        now = time.time()
        user_msgs = self.user_messages[guest_id]
        
        # 윈도우 밖의 메시지들 제거
        while user_msgs and user_msgs[0] <= now - self.window_seconds:
            user_msgs.popleft()
        
        return max(0, self.max_messages - len(user_msgs))


# 전역 WebSocket Rate Limiter 인스턴스
websocket_rate_limiter = WebSocketRateLimiter()


def check_websocket_rate_limit(guest_id: int) -> bool:
    """WebSocket 메시지 Rate Limit 확인"""
    return websocket_rate_limiter.is_message_allowed(guest_id)