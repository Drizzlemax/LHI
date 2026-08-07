"""
PANDORA Quiz Service Configuration
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="QUIZ_",
    )
    
    # Application
    app_name: str = "PANDORA Quiz Service"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8002
    workers: int = 4
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/quiz_db"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50
    
    # JWT/Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    
    # CORS
    cors_origins: list[str] = ["*"]
    
    # IRT Settings
    irt_initial_theta: float = 0.0
    irt_initial_std: float = 1.0
    irt_max_items_per_session: int = 50
    irt_convergence_threshold: float = 0.3
    
    # Quiz Settings
    quiz_default_time_limit_minutes: int = 30
    quiz_max_attempts: int = 3
    quiz_passing_score: float = 70.0
    
    # Telemetry
    otel_service_name: str = "quiz-service"
    otel_exporter_endpoint: str = "http://localhost:4317"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
