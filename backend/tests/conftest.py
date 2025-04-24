import pytest
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import contextlib

# 프로젝트 루트 경로를 시스템 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 모델 모듈 명시적으로 임포트 (테이블 생성을 위해 필요)
from db.postgres import Base
from models.guest_model import Guest
from models.gameroom_model import Gameroom, GameroomParticipant

# 테스트용 인메모리 SQLite 데이터베이스 설정
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL)

# 테스트용 세션 생성
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 테이블 생성 (중요: 모든 모델을 import한 후에 실행)
Base.metadata.create_all(bind=engine)

@pytest.fixture
def db_session():
    """각 테스트에 사용할 새로운 데이터베이스 세션 제공"""
    connection = engine.connect()
    
    # 트랜잭션 시작
    transaction = connection.begin()
    
    # 세션 생성
    session = TestingSessionLocal(bind=connection)
    
    try:
        yield session
    finally:
        # 세션 닫기
        session.close()
        
        # 트랜잭션이 여전히 활성 상태인 경우에만 롤백
        with contextlib.suppress(Exception):
            transaction.rollback()
            
        # 연결 닫기
        connection.close() 