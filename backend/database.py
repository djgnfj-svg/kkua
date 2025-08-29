from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from typing import Generator
import redis
from models.base import Base
import logging

# 환경 변수에서 데이터베이스 URL 가져오기
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/kkua_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# PostgreSQL 엔진 생성
engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # 연결 풀 크기 증가
    max_overflow=30,       # 최대 오버플로우 연결 수
    pool_pre_ping=True,
    pool_recycle=3600,     # 1시간마다 연결 재생성
    echo=os.getenv("DEBUG", "false").lower() == "true"
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis 클라이언트 생성
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

logger = logging.getLogger(__name__)


def create_tables():
    """데이터베이스 테이블 생성"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("데이터베이스 테이블이 생성되었습니다.")
    except Exception as e:
        logger.error(f"테이블 생성 중 오류 발생: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"데이터베이스 세션 오류: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_redis() -> redis.Redis:
    """Redis 클라이언트 반환"""
    return redis_client


async def test_connections():
    """데이터베이스와 Redis 연결 테스트"""
    try:
        # PostgreSQL 연결 테스트
        db = SessionLocal()
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("PostgreSQL 연결 성공")
        
        # Redis 연결 테스트
        redis_client.ping()
        logger.info("Redis 연결 성공")
        
        return True
    except Exception as e:
        logger.error(f"연결 테스트 실패: {e}")
        return False


def init_database():
    """데이터베이스 초기화"""
    import threading
    
    try:
        # 테이블 생성 (즉시 실행)
        create_tables()
        logger.info("데이터베이스 테이블 생성 완료")
        
        # 백그라운드에서 데이터 삽입 (서버 시작을 블로킹하지 않음)
        def background_data_init():
            try:
                logger.info("백그라운드에서 초기 데이터 삽입 시작...")
                from scripts.init_data import main as insert_initial_data
                insert_initial_data()
                logger.info("백그라운드 데이터 초기화 완료")
            except Exception as e:
                logger.error(f"백그라운드 데이터 초기화 실패: {e}")
        
        # 백그라운드 스레드로 실행
        init_thread = threading.Thread(target=background_data_init, daemon=True)
        init_thread.start()
        
        logger.info("데이터베이스 초기화 시작 (백그라운드 진행 중)")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        raise