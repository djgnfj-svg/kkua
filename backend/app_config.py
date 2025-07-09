import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:mysecretpassword@db:5432/mydb")
    
    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # Testing
    testing: bool = os.getenv("TESTING", "false").lower() == "true"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()