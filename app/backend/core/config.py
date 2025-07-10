"""
系统配置管理
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用设置"""
    
    # 基础配置
    APP_NAME: str = "软件架构师AI学习助手"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/tutor_db")
    
    # Redis配置
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # 安全配置
    ACCESS_KEY: Optional[str] = os.getenv("ACCESS_KEY")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    # AI服务配置
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # TTS配置
    TTS_ENGINE: str = "edge"  # edge, openai, valle-x
    TTS_VOICE_HOST: str = "zh-CN-YunxiNeural"
    TTS_VOICE_GUEST: str = "zh-CN-XiaoxiaoNeural"
    
    # 文件存储配置
    UPLOAD_DIR: str = "./data/uploads"
    PODCAST_DIR: str = "./data/podcasts"
    STATIC_DIR: str = "./static"
    
    # 学习配置
    DAILY_QUESTIONS_COUNT: int = 10
    PODCAST_DURATION_MINUTES: int = 15
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局设置实例
settings = Settings()

def get_settings() -> Settings:
    """获取设置实例"""
    return settings 