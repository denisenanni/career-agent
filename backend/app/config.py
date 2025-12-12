from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    
    # Database
    database_url: str = "postgresql://career_agent:career_agent_dev@localhost:5432/career_agent"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Anthropic
    anthropic_api_key: str = ""
    
    # Auth
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 1 week
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
