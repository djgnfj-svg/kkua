from fastapi import APIRouter, HTTPException, status, Depends
from db.redis import get_redis
from typing import Optional, List, Dict, Any

router = APIRouter(
    prefix="/word-game",
    tags=["word-game"]
)

@router.post("/redis/set", status_code=status.HTTP_200_OK)
async def set_redis_value(key: str, value: str, ttl: Optional[int] = None):
    # Redis 클라이언트 가져오기
    redis = get_redis()
    
    # 키-값 설정
    if ttl:
        redis.setex(key, ttl, value)
    else:
        redis.set(key, value)
    
    return {"message": f"키 '{key}'에 값 '{value}'를 저장했습니다"}

@router.get("/redis/get", status_code=status.HTTP_200_OK)
async def get_redis_value(key: str):
    # Redis 클라이언트 가져오기
    redis = get_redis()
    value = redis.get(key)
    
    if value is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"키 '{key}'를 찾을 수 없습니다")
    
    return {"key": key, "value": value}

@router.delete("/redis/delete", status_code=status.HTTP_200_OK)
async def delete_redis_key(key: str):
    # Redis 클라이언트 가져오기
    redis = get_redis()
    
    # 키 삭제
    result = redis.delete(key)
    
    if result == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"키 '{key}'를 찾을 수 없습니다")
    
    return {"message": f"키 '{key}'를 삭제했습니다"}

@router.get("/redis/exists", status_code=status.HTTP_200_OK)
async def check_redis_key_exists(key: str):
    # Redis 클라이언트 가져오기
    redis = get_redis()
    
    # 키 존재 여부 확인
    exists = redis.exists(key)
    
    return {"key": key, "exists": bool(exists)}

@router.post("/redis/expire", status_code=status.HTTP_200_OK)
async def set_redis_key_expiry(key: str, seconds: int):
    # Redis 클라이언트 가져오기
    redis = get_redis()
    
    # 키 존재 여부 확인
    if not redis.exists(key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"키 '{key}'를 찾을 수 없습니다")
    
    # 만료 시간 설정
    redis.expire(key, seconds)
    
    return {"message": f"키 '{key}'의 만료 시간을 {seconds}초로 설정했습니다"}

@router.get("/redis/ttl", status_code=status.HTTP_200_OK)
async def get_redis_key_ttl(key: str):
    # Redis 클라이언트 가져오기
    redis = get_redis()
    
    # 키 존재 여부 확인
    if not redis.exists(key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"키 '{key}'를 찾을 수 없습니다")
    
    # 남은 시간 조회
    ttl = redis.ttl(key)
    
    return {"key": key, "ttl": ttl}

@router.get("/redis/keys", status_code=status.HTTP_200_OK)
async def get_redis_keys(pattern: str = "*"):
    # Redis 클라이언트 가져오기
    redis = get_redis()
    
    # 패턴에 맞는 키 목록 조회
    keys = redis.keys(pattern)
    
    return {"pattern": pattern, "keys": keys}
