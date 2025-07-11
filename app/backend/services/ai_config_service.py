"""
AI配置管理服务
"""

import json
import base64
import httpx
import asyncio
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from datetime import datetime
import logging

from models.ai_config import AIProvider, AIConfiguration, ActiveAIService
from schemas.ai_config import AIProviderResponse, AIServiceConfig

logger = logging.getLogger(__name__)

class AIConfigService:
    """AI配置管理服务"""
    
    def __init__(self):
        # 生成密钥用于加密敏感信息
        self.fernet = Fernet(Fernet.generate_key())
        
        # 默认供应商配置
        self.default_providers = [
            {
                "name": "openai",
                "display_name": "OpenAI",
                "provider_type": "both",
                "base_url": "https://api.openai.com/v1",
                "supported_models": ["gpt-4", "gpt-3.5-turbo", "text-embedding-ada-002"]
            },
            {
                "name": "ollama", 
                "display_name": "Ollama (本地)",
                "provider_type": "both",
                "is_local": True,
                "base_url": "http://localhost:11434",
                "supported_models": []
            }
        ]
    
    def _encrypt_data(self, data: str) -> str:
        """加密敏感数据"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """解密敏感数据"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    async def initialize_default_providers(self, db: Session) -> None:
        """初始化默认供应商配置"""
        try:
            for provider_data in self.default_providers:
                existing = db.query(AIProvider).filter(
                    AIProvider.name == provider_data["name"]
                ).first()
                
                if not existing:
                    provider = AIProvider(**provider_data)
                    db.add(provider)
            
            db.commit()
            logger.info("默认AI供应商初始化完成")
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            db.rollback()
    
    async def get_providers(self, db: Session) -> List[AIProviderResponse]:
        """获取所有AI供应商"""
        providers = db.query(AIProvider).all()
        return [AIProviderResponse.from_orm(p) for p in providers]
    
    async def get_api_key(self, db: Session, provider_name: str) -> Optional[str]:
        """获取API密钥"""
        config = db.query(AIConfiguration).filter(
            AIConfiguration.config_key == f"{provider_name}_api_key"
        ).first()
        
        if not config:
            return None
        
        try:
            return self._decrypt_data(config.config_value)
        except:
            return None
    
    async def set_api_key(self, db: Session, provider_name: str, api_key: str) -> bool:
        """设置API密钥"""
        config_key = f"{provider_name}_api_key"
        
        # 加密存储
        encrypted_key = self._encrypt_data(api_key)
        
        config = db.query(AIConfiguration).filter(
            AIConfiguration.config_key == config_key
        ).first()
        
        if config:
            config.config_value = encrypted_key
        else:
            config = AIConfiguration(
                config_key=config_key,
                config_value=encrypted_key,
                config_type="encrypted",
                is_sensitive=True,
                description=f"{provider_name} API密钥"
            )
            db.add(config)
        
        db.commit()
        return True
    
    async def get_active_services(self, db: Session) -> AIServiceConfig:
        """获取当前激活的AI服务配置"""
        llm_service = db.query(ActiveAIService).filter(
            ActiveAIService.service_type == "llm"
        ).first()
        
        embedding_service = db.query(ActiveAIService).filter(
            ActiveAIService.service_type == "embedding"
        ).first()
        
        providers = await self.get_providers(db)
        
        return AIServiceConfig(
            llm_service=llm_service,
            embedding_service=embedding_service,
            available_providers=providers
        )
    
    async def set_active_service(self, db: Session, service_type: str, provider_name: str, model_name: str) -> bool:
        """设置激活的AI服务"""
        # 先停用相同类型的其他服务
        db.query(ActiveAIService).filter(
            ActiveAIService.service_type == service_type
        ).update({"is_active": False})
        
        # 查找现有服务或创建新服务
        service = db.query(ActiveAIService).filter(
            ActiveAIService.service_type == service_type
        ).first()
        
        if service:
            service.provider_name = provider_name
            service.model_name = model_name
            service.is_active = True
        else:
            service = ActiveAIService(
                service_type=service_type,
                provider_name=provider_name,
                model_name=model_name,
                is_active=True
            )
            db.add(service)
        
        db.commit()
        return True

    async def get_ollama_status(self, db: Session) -> Dict[str, Any]:
        """获取Ollama状态"""
        provider = db.query(AIProvider).filter(AIProvider.name == "ollama").first()
        if not provider:
            return {
                "is_running": False,
                "base_url": "http://localhost:11434",
                "available_models": []
            }
        
        try:
            async with httpx.AsyncClient() as client:
                # 检查Ollama是否运行
                response = await client.get(f"{provider.base_url}/api/version", timeout=5.0)
                if response.status_code != 200:
                    return {
                        "is_running": False,
                        "base_url": provider.base_url,
                        "available_models": []
                    }
                
                version_data = response.json()
                
                # 获取可用模型
                models_response = await client.get(f"{provider.base_url}/api/tags", timeout=5.0)
                models = []
                if models_response.status_code == 200:
                    models_data = models_response.json()
                    models = [
                        {
                            "name": model["name"],
                            "size": model.get("size"),
                            "digest": model.get("digest"),
                            "modified_at": model.get("modified_at")
                        }
                        for model in models_data.get("models", [])
                    ]
                
                    # 更新provider的支持模型列表
                    model_names = [model["name"] for model in models]
                    provider.supported_models = model_names
                    db.commit()
                
                return {
                    "is_running": True,
                    "version": version_data.get("version"),
                    "base_url": provider.base_url,
                    "available_models": models
                }
        
        except Exception as e:
            logger.warning(f"获取Ollama状态失败: {e}")
            return {
                "is_running": False,
                "base_url": provider.base_url,
                "available_models": []
            }
    
    async def pull_ollama_model(self, db: Session, model_name: str) -> Dict[str, Any]:
        """拉取Ollama模型"""
        provider = db.query(AIProvider).filter(AIProvider.name == "ollama").first()
        if not provider:
            return {"success": False, "message": "Ollama供应商未配置"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{provider.base_url}/api/pull",
                    json={"name": model_name},
                    timeout=300.0  # 5分钟超时
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": f"模型 {model_name} 拉取成功"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"模型拉取失败: {response.status_code}"
                    }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"模型拉取失败: {str(e)}"
            }

# 全局服务实例
ai_config_service = AIConfigService()