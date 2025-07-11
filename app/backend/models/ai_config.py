"""
AI配置数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from core.database import Base

class AIProvider(Base):
    """AI供应商配置"""
    __tablename__ = "ai_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)  # openai, claude, ollama
    display_name = Column(String(200))  # 显示名称
    provider_type = Column(String(50))  # llm, embedding, both
    is_enabled = Column(Boolean, default=True)
    is_local = Column(Boolean, default=False)  # 是否为本地服务
    
    # 连接配置
    base_url = Column(String(500))  # API base URL
    api_version = Column(String(50))  # API版本
    
    # 支持的模型列表 (JSON格式)
    supported_models = Column(JSON)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<AIProvider(id={self.id}, name='{self.name}')>"

class AIConfiguration(Base):
    """AI配置设置"""
    __tablename__ = "ai_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, index=True)
    config_value = Column(Text)
    config_type = Column(String(50))  # string, json, encrypted
    description = Column(Text)
    is_sensitive = Column(Boolean, default=False)  # 是否为敏感信息（如API key）
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<AIConfiguration(key='{self.config_key}')>"

class ActiveAIService(Base):
    """当前激活的AI服务配置"""
    __tablename__ = "active_ai_services"
    
    id = Column(Integer, primary_key=True, index=True)
    service_type = Column(String(50), unique=True, index=True)  # llm, embedding
    provider_name = Column(String(100))  # 对应 AIProvider.name
    model_name = Column(String(200))  # 使用的具体模型
    is_active = Column(Boolean, default=True)
    
    # 额外配置参数 (JSON格式)
    extra_config = Column(JSON)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ActiveAIService(type='{self.service_type}', provider='{self.provider_name}')>" 