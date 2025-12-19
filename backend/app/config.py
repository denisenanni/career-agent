from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
import sys


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

    # CORS - comma-separated list of allowed origins
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @field_validator('jwt_secret')
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        """Ensure JWT secret is not using default value in production"""
        if v == "dev-secret-change-me":
            # Allow in development/testing, but warn
            environment = info.data.get('environment', 'development')
            if environment == 'production':
                print("FATAL: Cannot use default JWT secret in production!", file=sys.stderr)
                raise ValueError(
                    "JWT_SECRET must be set to a strong random value in production. "
                    "Generate one with: openssl rand -base64 32"
                )
            else:
                print("WARNING: Using default JWT secret. Set JWT_SECRET environment variable.", file=sys.stderr)

        # Ensure minimum length
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long for security")

        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
