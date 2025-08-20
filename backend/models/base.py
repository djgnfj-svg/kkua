from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

# 데이터베이스 테이블의 기본 클래스
metadata = MetaData()
Base = declarative_base(metadata=metadata)