"""
AI配置相关的Pydantic模式
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime

# AI供应商相关模式
class AIProviderBase(BaseModel):
    name: str = Field(..., description="供应商标识名")
    display_name: str = Field(..., description="显示名称")
    provider_type: str = Field(..., description="类型: llm, embedding, both")
    is_enabled: bool = Field(True, description="是否启用")
    is_local: bool = Field(False, description="是否为本地服务")
    base_url: Optional[str] = Field(None, description="API基础URL")
    api_version: Optional[str] = Field(None, description="API版本")
    supported_models: List[str] = Field(default=[], description="支持的模型列表")

class AIProviderCreate(AIProviderBase):
    pass

class AIProviderUpdate(BaseModel):
    display_name: Optional[str] = None
    provider_type: Optional[str] = None
    is_enabled: Optional[bool] = None
    is_local: Optional[bool] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    supported_models: Optional[List[str]] = None

class AIProviderResponse(AIProviderBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# AI配置相关模式
class AIConfigurationBase(BaseModel):
    config_key: str = Field(..., description="配置键")
    config_value: str = Field(..., description="配置值")
    config_type: str = Field("string", description="配置类型")
    description: Optional[str] = Field(None, description="配置描述")
    is_sensitive: bool = Field(False, description="是否敏感信息")

class AIConfigurationCreate(AIConfigurationBase):
    pass

class AIConfigurationUpdate(BaseModel):
    config_value: Optional[str] = None
    description: Optional[str] = None
    is_sensitive: Optional[bool] = None

class AIConfigurationResponse(AIConfigurationBase):
    id: int
    # 敏感信息在响应中隐藏
    config_value: Optional[str] = Field(None, description="配置值（敏感信息会被隐藏）")
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# 激活的AI服务相关模式
class ActiveAIServiceBase(BaseModel):
    service_type: str = Field(..., description="服务类型: llm, embedding")
    provider_name: str = Field(..., description="供应商名称")
    model_name: str = Field(..., description="模型名称")
    is_active: bool = Field(True, description="是否激活")
    extra_config: Optional[Dict[str, Any]] = Field(default={}, description="额外配置")

class ActiveAIServiceCreate(ActiveAIServiceBase):
    pass

class ActiveAIServiceUpdate(BaseModel):
    provider_name: Optional[str] = None
    model_name: Optional[str] = None
    is_active: Optional[bool] = None
    extra_config: Optional[Dict[str, Any]] = None

class ActiveAIServiceResponse(ActiveAIServiceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# 综合管理模式
class AIServiceConfig(BaseModel):
    """AI服务完整配置"""
    llm_service: Optional[ActiveAIServiceResponse] = None
    embedding_service: Optional[ActiveAIServiceResponse] = None
    available_providers: List[AIProviderResponse] = []

class AIProviderTestRequest(BaseModel):
    """测试AI供应商连接请求"""
    provider_name: str
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    test_type: str = Field("connection", description="测试类型: connection, model")

class AIProviderTestResponse(BaseModel):
    """测试AI供应商连接响应"""
    success: bool
    message: str
    response_time: Optional[float] = None
    model_info: Optional[Dict[str, Any]] = None

# 密钥管理相关模式
class APIKeyCreate(BaseModel):
    provider_name: str = Field(..., description="供应商名称")
    api_key: str = Field(..., description="API密钥")
    key_name: Optional[str] = Field(None, description="密钥名称")

class APIKeyUpdate(BaseModel):
    api_key: str = Field(..., description="新的API密钥")

class APIKeyResponse(BaseModel):
    provider_name: str
    key_name: Optional[str]
    masked_key: str = Field(..., description="掩码后的密钥")
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

# Ollama特定模式
class OllamaModelInfo(BaseModel):
    name: str
    size: Optional[int] = None
    digest: Optional[str] = None
    modified_at: Optional[datetime] = None

class OllamaStatusResponse(BaseModel):
    is_running: bool
    version: Optional[str] = None
    available_models: List[OllamaModelInfo] = []
    base_url: str 