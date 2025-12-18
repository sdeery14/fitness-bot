"""Application configuration using Pydantic settings."""
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "fitness_bot"
    DATABASE_URL: str
    DATABASE_URL_LOCAL: str | None = None  # Optional: for local scripts outside Docker
    
    # Redis
    REDIS_URL: str
    
    # OpenAI
    OPENAI_API_KEY: str
    MODEL_NAME: str = "gpt-5.1"  # Default model, can be overridden via env
    
    # JWT Authentication
    JWT_SECRET: str  # Used by AuthService
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 days

    # Legacy aliases for backward compatibility
    @property
    def SECRET_KEY(self) -> str:
        return self.JWT_SECRET

    @property
    def ALGORITHM(self) -> str:
        return self.JWT_ALGORITHM

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    
    # Application
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    
    # USDA FoodData Central API
    USDA_API_KEY: str | None = None
    
    # Celery
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    
    # MLflow
    MLFLOW_TRACKING_URI: str | None = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    def get_database_url(self) -> str:
        """Get the appropriate database URL for the current context.
        
        Returns DATABASE_URL_LOCAL if set (for local scripts), otherwise DATABASE_URL.
        This allows local scripts to use localhost:5432 while Docker uses postgres:5432.
        """
        return self.DATABASE_URL_LOCAL or self.DATABASE_URL


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings.
    
    Returns:
        Settings instance
    """
    return settings
