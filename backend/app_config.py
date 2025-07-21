import os
import secrets
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Security
    secret_key: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:CHANGE_ME_IN_PRODUCTION@db:5432/mydb")
    database_user: str = os.getenv("DATABASE_USER", "postgres")
    database_password: str = os.getenv("DATABASE_PASSWORD", "CHANGE_ME_IN_PRODUCTION")
    database_name: str = os.getenv("DATABASE_NAME", "mydb")
    database_host: str = os.getenv("DATABASE_HOST", "db")
    database_port: int = int(os.getenv("DATABASE_PORT", "5432"))
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
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
    
    # Session Configuration
    session_timeout: int = int(os.getenv("SESSION_TIMEOUT", "86400"))  # 24 hours
    session_secure: bool = os.getenv("SESSION_SECURE", "false").lower() == "true"
    session_samesite: str = os.getenv("SESSION_SAMESITE", "lax")
    
    # Security Headers
    enable_security_headers: bool = os.getenv("ENABLE_SECURITY_HEADERS", "true").lower() == "true"
    hsts_max_age: int = int(os.getenv("HSTS_MAX_AGE", "31536000"))  # 1 year
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def validate_production_settings(self):
        """프로덕션 환경에서 보안 설정 검증"""
        if self.environment == "production":
            if "CHANGE_ME_IN_PRODUCTION" in self.database_password:
                raise ValueError("프로덕션 환경에서는 데이터베이스 비밀번호를 변경해야 합니다")
            if "CHANGE_ME_IN_PRODUCTION" in self.database_url:
                raise ValueError("프로덕션 환경에서는 데이터베이스 URL을 변경해야 합니다")
            if self.debug:
                raise ValueError("프로덕션 환경에서는 DEBUG를 False로 설정해야 합니다")
            if not self.session_secure:
                raise ValueError("프로덕션 환경에서는 SESSION_SECURE를 True로 설정해야 합니다")


settings = Settings()

# 프로덕션 환경 설정 검증
if hasattr(settings, 'validate_production_settings'):
    settings.validate_production_settings()