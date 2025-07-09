from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.postgres import Base, engine
from routers import (
    auth_router,
    guests_router,
    gamerooms_router,
    gameroom_ws_router,
    gameroom_actions_router,
)
from fastapi.openapi.utils import get_openapi
from app_config import settings

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
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.environment == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(auth_router.router)  # 인증 API
app.include_router(guests_router.router)
app.include_router(gamerooms_router.router)  # 기본 CRUD 기능
app.include_router(gameroom_actions_router.router)  # 게임룸 액션 기능
app.include_router(gameroom_ws_router.router)  # 웹소켓 기능


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
    return {"status": "healthy", "environment": settings.environment}


# OpenAPI 스키마 커스터마이징 (선택 사항)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # WebSocket 태그에 대한 설명 추가
    openapi_schema["tags"] = [
        {
            "name": "websockets",
            "description": "웹소켓 관련 API (웹소켓 자체는 Swagger에서 테스트할 수 없음)",
        },
        # 기타 태그들...
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
