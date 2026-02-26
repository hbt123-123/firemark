from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Plan Agent Backend"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/plan_agent_db"
    
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # LLM (Chat) API
    LLM_API_KEY: str = ""
    LLM_API_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL_NAME: str = "gpt-4"
    
    # Embedding API (支持多个 API 自动切换)
    # 格式: [{"url": "https://api.openai.com/v1", "key": "sk-xxx", "model": "text-embedding-3-small"}, ...]
    EMBEDDING_PROVIDERS: str = "[]"  # JSON 字符串格式
    
    # 兼容旧版单 API 配置
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_API_BASE_URL: str = "https://api.openai.com/v1"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False  # 设为 True 启用 Redis
    CACHE_TTL_DEFAULT: int = 300  # 默认缓存时间 (秒)
    SESSION_CACHE_TTL: int = 3600  # 会话缓存时间 (1小时)
    
    DEBUG: bool = True
    
    SERP_API_KEY: str = ""
    JPUSH_APP_KEY: str = ""
    JPUSH_MASTER_SECRET: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def validate_settings():
    """验证必需的配置项"""
    missing = []
    if not settings.LLM_API_KEY:
        missing.append('LLM_API_KEY')
    if not settings.DATABASE_URL or 'localhost' in settings.DATABASE_URL:
        # 开发环境允许 localhost
        pass
    if missing:
        import warnings
        warnings.warn(f"Missing recommended config: {', '.join(missing)}")
    
    # 生产环境必须设置 JWT secret
    if 'your-super-secret' in settings.JWT_SECRET_KEY:
        import warnings
        warnings.warn("WARNING: Using default JWT_SECRET_KEY in production is not recommended!")

validate_settings()
