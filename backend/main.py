"""
끄아(KKUA) V2 - FastAPI 메인 애플리케이션
Pure WebSocket 아키텍처 기반 실시간 멀티플레이어 한국어 끝말잇기 게임
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 데이터베이스 및 Redis 연결
from database import init_database, test_connections


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시
    logger.info("끄아(KKUA) V2 서버 시작 중...")
    
    try:
        # 데이터베이스 연결 테스트
        connection_ok = await test_connections()
        if not connection_ok:
            logger.error("데이터베이스/Redis 연결 실패")
            raise Exception("데이터베이스 연결 실패")
        
        # 데이터베이스 초기화
        if os.getenv("INIT_DB", "true").lower() == "true":
            init_database()
        
        logger.info("끄아(KKUA) V2 서버 시작 완료")
        
        yield
        
    except Exception as e:
        logger.error(f"서버 시작 실패: {e}")
        raise
    
    # 종료 시
    logger.info("끄아(KKUA) V2 서버 종료 중...")


# FastAPI 앱 생성
app = FastAPI(
    title="끄아(KKUA) V2",
    description="Pure WebSocket 아키텍처 기반 실시간 멀티플레이어 한국어 끝말잇기 게임",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 설정
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 신뢰할 수 있는 호스트 설정 (프로덕션용)
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # 실제 배포시에는 구체적인 도메인 설정
    )


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "끄아(KKUA) V2 - Pure WebSocket 아키텍처 한국어 끝말잇기 게임",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Pure WebSocket 통신",
            "아이템 시스템",
            "실시간 타이머",
            "단어 검증",
            "게임 리포트",
            "포괄적인 로깅"
        ]
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    try:
        # 데이터베이스와 Redis 연결 상태 확인
        connection_status = await test_connections()
        
        return {
            "status": "healthy" if connection_status else "unhealthy",
            "database": "connected" if connection_status else "disconnected",
            "redis": "connected" if connection_status else "disconnected",
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/api/status")
async def api_status():
    """API 상태 정보"""
    return {
        "api_version": "2.0.0",
        "phase": "Phase 1 - 백엔드 핵심 인프라",
        "implemented_features": [
            "데이터베이스 스키마",
            "SQLAlchemy 모델",
            "Redis 데이터 구조",
            "기본 데이터 초기화"
        ],
        "next_features": [
            "WebSocket 인프라",
            "게임 엔진",
            "단어 검증 서비스",
            "아이템 시스템"
        ]
    }


# Phase 2에서 추가될 라우터들
# from routers import websocket_router, auth_router, game_router
# app.include_router(websocket_router.router, prefix="/ws", tags=["websocket"])
# app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
# app.include_router(game_router.router, prefix="/api/game", tags=["game"])

if __name__ == "__main__":
    import uvicorn
    
    # 개발 환경에서만 직접 실행
    if os.getenv("ENVIRONMENT", "development") == "development":
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )