from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.postgres import Base, engine
from routers import (
    auth_router,
    guests_router,
    gamerooms_router,
    gameroom_ws_router,
    gameroom_actions_router,
    game_api_router,
)
from fastapi.openapi.utils import get_openapi
from app_config import settings
from middleware.logging_middleware import RequestLoggingMiddleware
from middleware.exception_handler import GlobalExceptionHandler
from config.logging_config import setup_logging
import logging
from contextlib import asynccontextmanager
from datetime import datetime

# 로깅 초기화
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 수명 주기 관리"""
    # 시작 시
    logger.info("애플리케이션 시작 중...")
    
    # Redis 연결 초기화
    try:
        from services.redis_game_service import get_redis_game_service
        redis_service = await get_redis_game_service()
        logger.info("Redis 게임 서비스 초기화 완료")
    except Exception as e:
        logger.error(f"Redis 게임 서비스 초기화 실패: {e}")
        # Redis 실패 시에도 앱은 계속 실행되도록 함
    
    yield
    
    # 종료 시
    logger.info("애플리케이션 종료 중...")
    try:
        from services.redis_game_service import get_redis_game_service
        redis_service = await get_redis_game_service()
        await redis_service.disconnect()
        logger.info("Redis 연결 종료 완료")
    except Exception as e:
        logger.error(f"Redis 연결 종료 실패: {e}")


app = FastAPI(
    title="끄아 (KKUA) - 게임방 관리 API",
    description="""
    ## 끄아 (KKUA) - 실시간 끝말잇기 게임 API
    
    PostgreSQL을 사용한 게임방 및 게임 관리 API
    
    ### 웹소켓 API
    
    게임룸 관련 실시간 기능은 웹소켓을 통해 제공됩니다:
    
    **연결 URL**: `ws://서버주소/ws/gamerooms/{room_id}/{guest_uuid}`
    
    자세한 정보는 `/websockets/documentation` 엔드포인트를 참조하세요.
    """,
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

logger.info(f"Starting KKUA application - Environment: {settings.environment}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(GlobalExceptionHandler)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router.router)
app.include_router(guests_router.router)
app.include_router(gamerooms_router.router)
app.include_router(gameroom_actions_router.router)
app.include_router(gameroom_ws_router.router)
app.include_router(game_api_router.router)


@app.get("/")
async def root():
    return {
        "message": "끄아 (KKUA) - 실시간 끝말잇기 게임 API에 오신 것을 환영합니다!",
        "version": "1.0.0",
        "environment": settings.environment,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """기본 헬스체크 엔드포인트"""
    return {"status": "healthy", "environment": settings.environment}


@app.get("/health/detailed")
async def detailed_health_check():
    """상세 헬스체크 - 모든 의존성 상태 확인"""
    health_status = {
        "status": "healthy",
        "environment": settings.environment,
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # Redis 연결 상태 확인
    try:
        from services.redis_game_service import get_redis_game_service
        redis_service = await get_redis_game_service()
        is_redis_connected = await redis_service.is_connected()
        health_status["services"]["redis"] = {
            "status": "healthy" if is_redis_connected else "unhealthy",
            "connected": is_redis_connected
        }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # PostgreSQL 연결 상태 확인
    try:
        from db.postgres import get_db
        db_session = next(get_db())
        db_session.execute("SELECT 1")
        db_session.close()
        health_status["services"]["postgresql"] = {
            "status": "healthy",
            "connected": True
        }
    except Exception as e:
        health_status["services"]["postgresql"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    
    # 전체 상태 결정
    all_services_healthy = all(
        service.get("status") == "healthy" or service.get("status") == "disabled"
        for service in health_status["services"].values()
    )
    
    if not all_services_healthy:
        health_status["status"] = "degraded"
    
    return health_status


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["tags"] = [
        {
            "name": "websockets",
            "description": "웹소켓 관련 API (웹소켓 자체는 Swagger에서 테스트할 수 없음)",
        },
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=settings.debug
    )
