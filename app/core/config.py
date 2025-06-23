"""
애플리케이션 설정
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 설정
    app_name: str = "Libera FastAPI"
    version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 데이터베이스 설정 (비동기만 지원)
    async_database_url: str = "postgresql+asyncpg://libetion_user:libetion_password@localhost:5432/libetion_db"
    
    # CORS 설정
    cors_origins: List[str] = ["*"]
    
    # 보안 설정
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 파일 업로드 설정
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    upload_dir: str = "uploads"
    allowed_extensions: List[str] = [".pdf"]
    
    # 로깅 설정
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API 설정
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Libetion PDF Extraction System"
    
    # 파서 설정
    use_enhanced_parser: bool = os.getenv("USE_ENHANCED_PARSER", "true").lower() == "true"
    
    # AI 백업 설정 (선택적)
    enable_ai_backup: bool = os.getenv("ENABLE_AI_BACKUP", "false").lower() == "true"
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY", None)

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 