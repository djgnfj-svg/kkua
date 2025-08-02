"""
Sentry 모니터링 설정

실시간 에러 추적, 성능 모니터링, 사용자 세션 분석을 위한 Sentry 통합
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging

from app_config import settings


def init_sentry():
    """Sentry 모니터링 초기화"""
    
    if not settings.sentry_dsn:
        logging.info("Sentry DSN이 설정되지 않았습니다. 모니터링이 비활성화됩니다.")
        return
    
    # 통합 설정
    integrations = [
        FastApiIntegration(
            auto_enable=True,
            transaction_style="endpoint"
        ),
        SqlalchemyIntegration(),
        RedisIntegration(),
        LoggingIntegration(
            level=logging.INFO,        # 캡처할 최소 로그 레벨
            event_level=logging.ERROR  # Sentry로 이벤트를 보낼 최소 레벨
        ),
    ]
    
    # Sentry 초기화
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        integrations=integrations,
        
        # 성능 모니터링
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        
        # 릴리스 정보 (나중에 CI/CD에서 설정)
        release=f"kkua@{settings.environment}",
        
        # 추가 설정
        attach_stacktrace=True,
        send_default_pii=False,  # 개인정보 전송 비활성화
        max_breadcrumbs=50,
        
        # 환경별 설정
        debug=settings.debug if settings.environment == "development" else False,
    )
    
    logging.info(f"Sentry 모니터링이 초기화되었습니다. Environment: {settings.sentry_environment}")


def capture_game_event(event_type: str, data: dict, user_id: str = None):
    """게임 관련 사용자 정의 이벤트 캡처"""
    
    with sentry_sdk.push_scope() as scope:
        # 이벤트 컨텍스트 설정
        scope.set_tag("event_type", event_type)
        scope.set_tag("service", "game")
        
        if user_id:
            scope.set_user({"id": user_id})
        
        # 게임 데이터 추가
        scope.set_context("game_data", data)
        
        # 커스텀 메시지로 이벤트 캡처
        sentry_sdk.capture_message(
            f"Game Event: {event_type}",
            level="info"
        )


def capture_websocket_error(error: Exception, room_id: str = None, user_id: str = None):
    """WebSocket 관련 에러 캡처"""
    
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("error_type", "websocket")
        scope.set_tag("service", "websocket")
        
        if room_id:
            scope.set_tag("room_id", room_id)
        
        if user_id:
            scope.set_user({"id": user_id})
        
        # WebSocket 컨텍스트 추가
        scope.set_context("websocket", {
            "room_id": room_id,
            "user_id": user_id,
            "error_type": type(error).__name__
        })
        
        sentry_sdk.capture_exception(error)


def capture_redis_error(error: Exception, operation: str = None, key: str = None):
    """Redis 관련 에러 캡처"""
    
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("error_type", "redis")
        scope.set_tag("service", "redis")
        
        if operation:
            scope.set_tag("redis_operation", operation)
        
        # Redis 컨텍스트 추가
        scope.set_context("redis", {
            "operation": operation,
            "key": key,
            "error_type": type(error).__name__
        })
        
        sentry_sdk.capture_exception(error)


def capture_database_error(error: Exception, query: str = None, table: str = None):
    """데이터베이스 관련 에러 캡처"""
    
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("error_type", "database")
        scope.set_tag("service", "database")
        
        if table:
            scope.set_tag("db_table", table)
        
        # 데이터베이스 컨텍스트 추가
        scope.set_context("database", {
            "table": table,
            "query_preview": query[:200] if query else None,  # 쿼리 일부만 포함
            "error_type": type(error).__name__
        })
        
        sentry_sdk.capture_exception(error)