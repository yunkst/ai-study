
"""应用配置模块

包含应用的所有配置设置。
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres:postgres123@localhost:5432/ai_study"

    # JWT Configuration
    JWT_SECRET: str = "your-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Dify AI Service Configuration
    DIFY_API_URL: str = "http://localhost:8080"
    DIFY_API_KEY: str = "your-dify-api-key"

    # File Upload Configuration
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
