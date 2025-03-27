from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# PostgreSQL DB 연결 설정
DATABASE_URL = "postgresql://postgres:mysecretpassword@db:5432/mydb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# 의존성 주입을 위한 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 