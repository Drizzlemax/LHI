"""
PANDORA Learning Service Configuration
"""
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = "PANDORA Learning Service"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8003
    reload: bool = False
    
    # Database (PostgreSQL)
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/pandora_learning"
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Neo4j Graph Database
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"
    neo4j_database: str = "neo4j"
    
    # Redis
    redis_url: str = "redis://localhost:6379/2"
    
    # Content Service (for fetching content metadata)
    content_service_url: str = "http://localhost:8001"
    
    # User Service (for user context)
    user_service_url: str = "http://localhost:8000"
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    # OpenTelemetry
    otel_service_name: str = "learning-service"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_enabled: bool = True
    
    # Learning Configuration
    max_learning_path_length: int = 50
    default_difficulty_weight: float = 0.3
    default_interest_weight: float = 0.3
    default_completion_weight: float = 0.4
    
    # Recommendation Settings
    similar_users_count: int = 10
    recommendations_count: int = 20
    min_content_for_recommendations: int = 5
    
    # Quiz Settings
    default_quiz_time_limit_minutes: int = 30
    passing_score_percentage: float = 70.0
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if isinstance(self.cors_origins, str):
            return [o.strip() for o in self.cors_origins.split(",")]
        return self.cors_origins


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
