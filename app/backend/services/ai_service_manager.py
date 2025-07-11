"""
AI服务管理器 - 动态管理AI供应商和服务
"""

import asyncio
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
import logging

from services.ai_providers import AIProviderFactory, AIProvider
from services.ai_config_service import ai_config_service
from models.ai_config import ActiveAIService

logger = logging.getLogger(__name__)

class AIServiceManager:
    """AI服务管理器"""
    
    def __init__(self):
        self.llm_provider: Optional[AIProvider] = None
        self.embedding_provider: Optional[AIProvider] = None
        self._initialized = False
    
    async def initialize(self, db: Session) -> None:
        """初始化AI服务管理器"""
        try:
            await ai_config_service.initialize_default_providers(db)
            await self._load_active_services(db)
            self._initialized = True
            logger.info("AI服务管理器初始化完成")
        except Exception as e:
            logger.error(f"AI服务管理器初始化失败: {e}")
    
    async def _load_active_services(self, db: Session) -> None:
        """加载当前激活的AI服务"""
        try:
            # 获取激活的LLM服务
            llm_service = db.query(ActiveAIService).filter(
                ActiveAIService.service_type == "llm",
                ActiveAIService.is_active == True
            ).first()
            
            if llm_service:
                self.llm_provider = await self._create_provider(db, llm_service)
                logger.info(f"LLM服务已加载: {llm_service.provider_name}/{llm_service.model_name}")
            
        except Exception as e:
            logger.error(f"加载激活服务失败: {e}")
    
    async def _create_provider(self, db: Session, service: ActiveAIService) -> Optional[AIProvider]:
        """创建AI提供者实例"""
        try:
            # 获取API密钥
            api_key = await ai_config_service.get_api_key(db, service.provider_name)
            
            # 获取供应商配置
            from models.ai_config import AIProvider as AIProviderModel
            provider_config = db.query(AIProviderModel).filter(
                AIProviderModel.name == service.provider_name
            ).first()
            
            if not provider_config:
                logger.error(f"找不到供应商配置: {service.provider_name}")
                return None
            
            # 创建配置字典
            config = {
                "name": service.provider_name,
                "api_key": api_key,
                "base_url": provider_config.base_url,
                "model_name": service.model_name
            }
            
            # 创建提供者实例
            provider = AIProviderFactory.create_provider(service.provider_name, config)
            return provider
            
        except Exception as e:
            logger.error(f"创建提供者失败: {e}")
            return None
    
    async def get_llm_provider(self, db: Session) -> Optional[AIProvider]:
        """获取LLM提供者"""
        if not self._initialized:
            await self.initialize(db)
        
        if not self.llm_provider:
            await self._load_active_services(db)
        
        return self.llm_provider
    
    async def generate_text(self, db: Session, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """使用当前LLM提供者生成文本"""
        provider = await self.get_llm_provider(db)
        if not provider:
            raise Exception("没有可用的LLM提供者")
        
        return await provider.generate_text(prompt, max_tokens, temperature)

# 全局AI服务管理器实例
ai_service_manager = AIServiceManager()