# 데이터베이스 초기화
from .postgres import Base, engine

Base.metadata.create_all(bind=engine) 