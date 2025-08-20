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
# credentials=True일 때는 wildcard "*" 사용 불가 (CORS 정책)
# 개발 모드에서도 구체적인 도메인만 사용

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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
        "phase": "Phase 2 - WebSocket 인프라 완료",
        "implemented_features": [
            "데이터베이스 스키마",
            "SQLAlchemy 모델", 
            "Redis 데이터 구조",
            "기본 데이터 초기화",
            "JWT 토큰 인증",
            "WebSocket 연결 관리자",
            "메시지 라우터",
            "게임 이벤트 핸들러",
            "WebSocket 엔드포인트"
        ],
        "next_features": [
            "게임 엔진 완성",
            "단어 검증 서비스",
            "아이템 시스템 완성",
            "REST API 엔드포인트"
        ]
    }


# 인증 및 API 관련 import
from auth import AuthService
from pydantic import BaseModel
from fastapi import HTTPException

# Redis 관련 import (일찍 import 필요)
from redis_models import RedisGameManager
from database import get_redis

# Redis 게임 매니저 인스턴스 (전역 변수로 선언)
redis_game_manager = RedisGameManager(get_redis())

# Request/Response 모델
class GuestLoginRequest(BaseModel):
    nickname: str

class AuthResponse(BaseModel):
    success: bool
    user_id: str
    nickname: str
    session_token: str
    message: str

# AuthService 인스턴스
auth_service = AuthService()

# REST API 엔드포인트
@app.post("/auth/login", response_model=AuthResponse)
async def guest_login(request: GuestLoginRequest):
    """게스트 로그인"""
    try:
        # 닉네임 검증
        if not request.nickname or len(request.nickname.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="닉네임은 최소 2글자 이상이어야 합니다"
            )
        
        if len(request.nickname.strip()) > 12:
            raise HTTPException(
                status_code=400,
                detail="닉네임은 최대 12글자까지 가능합니다"
            )
        
        nickname = request.nickname.strip()
        
        # 간단한 사용자 ID 생성 (실제로는 DB에서 관리해야 함)
        import time
        user_id = int(time.time() * 1000) % 1000000  # 임시 ID 생성
        
        # JWT 토큰 생성
        token = auth_service.create_guest_token(user_id, nickname)
        
        logger.info(f"게스트 로그인 성공: {nickname} (ID: {user_id})")
        
        return AuthResponse(
            success=True,
            user_id=str(user_id),
            nickname=nickname,
            session_token=token,
            message=f"환영합니다, {nickname}님!"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"게스트 로그인 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="로그인 처리 중 오류가 발생했습니다"
        )

@app.get("/auth/me")
async def get_current_user():
    """현재 사용자 정보 (토큰 검증용)"""
    # TODO: JWT 토큰 헤더에서 사용자 정보 추출
    return {"message": "인증된 사용자 정보 조회는 아직 구현되지 않았습니다"}

# 임시 게임룸 데이터 (메모리에 저장)
temporary_rooms = []

class CreateRoomRequest(BaseModel):
    name: str
    max_players: int = 4

@app.get("/gamerooms")
async def list_gamerooms():
    """게임룸 목록 조회"""
    return temporary_rooms

@app.post("/gamerooms")
async def create_gameroom(request: CreateRoomRequest):
    """게임룸 생성"""
    try:
        if not request.name or len(request.name.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="방 이름은 최소 2글자 이상이어야 합니다"
            )
        
        if request.max_players < 2 or request.max_players > 8:
            raise HTTPException(
                status_code=400,
                detail="최대 플레이어 수는 2-8명 사이여야 합니다"
            )
        
        import time
        from datetime import datetime
        
        room_id = f"room_{int(time.time() * 1000)}"
        
        new_room = {
            "id": room_id,
            "name": request.name.strip(),
            "maxPlayers": request.max_players,
            "currentPlayers": 1,  # 방을 만든 사람
            "status": "waiting",
            "createdAt": datetime.now().isoformat(),
            "players": []
        }
        
        temporary_rooms.append(new_room)
        
        # Redis에 빈 게임 상태 생성 (실제 플레이어는 WebSocket 입장 시 추가)
        logger.info(f"Redis 게임 상태 준비: {room_id}")
        # 첫 번째 플레이어가 WebSocket으로 입장할 때 방장으로 설정됨
        
        logger.info(f"게임룸 생성: {request.name} (ID: {room_id})")
        
        return {"room_id": room_id, **new_room}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"게임룸 생성 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="방 생성 중 오류가 발생했습니다"
        )

@app.post("/gamerooms/{room_id}/join")
async def join_gameroom(room_id: str):
    """게임룸 참가"""
    # 임시 구현
    for room in temporary_rooms:
        if room["id"] == room_id:
            if room["currentPlayers"] < room["maxPlayers"]:
                room["currentPlayers"] += 1
                return {"message": f"{room['name']} 방에 참가했습니다", "room": room}
            else:
                raise HTTPException(status_code=400, detail="방이 가득 찼습니다")
    
    raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다")

@app.post("/gamerooms/{room_id}/leave")
async def leave_gameroom(room_id: str):
    """게임룸 나가기"""
    # 임시 구현
    for room in temporary_rooms:
        if room["id"] == room_id:
            room["currentPlayers"] = max(0, room["currentPlayers"] - 1)
            if room["currentPlayers"] == 0:
                temporary_rooms.remove(room)
            return {"message": "방에서 나갔습니다"}
    
    raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다")

# 아이템 관련 API
@app.get("/users/{user_id}/inventory")
async def get_user_inventory(user_id: int):
    """사용자 아이템 인벤토리 조회"""
    try:
        from services.item_service import get_item_service
        item_service = get_item_service()
        
        inventory = await item_service.get_user_inventory(user_id)
        return {
            "success": True,
            "inventory": inventory
        }
        
    except Exception as e:
        logger.error(f"인벤토리 조회 실패: user_id={user_id}, error={e}")
        raise HTTPException(
            status_code=500,
            detail="인벤토리 조회 중 오류가 발생했습니다"
        )

@app.get("/items/list")
async def list_available_items():
    """사용 가능한 아이템 목록 조회"""
    try:
        from services.item_service import get_item_service
        item_service = get_item_service()
        
        items = await item_service.get_all_items()
        return {
            "success": True,
            "items": items
        }
        
    except Exception as e:
        logger.error(f"아이템 목록 조회 실패: error={e}")
        raise HTTPException(
            status_code=500,
            detail="아이템 목록 조회 중 오류가 발생했습니다"
        )

# Phase 2 라우터 추가
from websocket.websocket_endpoint import get_websocket_router

# WebSocket 라우터 등록
websocket_router = get_websocket_router()
app.include_router(websocket_router, tags=["websocket"])

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