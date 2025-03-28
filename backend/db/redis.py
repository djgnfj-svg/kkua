import redis

# Redis DB 연결 설정
REDIS_URL = "redis://redis:6379/0"

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Redis 클라이언트 가져오기
def get_redis():
    return redis_client 