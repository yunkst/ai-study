"""
AI提供者抽象层 - 支持多种AI供应商
"""

import json
import httpx
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

class AIProvider(ABC):
    """AI提供者抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", "unknown")
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")
        self.model_name = config.get("model_name")
    
    @abstractmethod
    async def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """生成文本"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        pass

class OpenAIProvider(AIProvider):
    """OpenAI提供者"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化OpenAI客户端"""
        if self.api_key:
            import openai
            self.client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
    
    async def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """生成文本"""
        if not self.client:
            raise Exception("OpenAI客户端未初始化")
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name or "gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI文本生成失败: {str(e)}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        if not self.client:
            return {"success": False, "message": "客户端未初始化"}
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name or "gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            return {
                "success": True,
                "message": "OpenAI连接成功",
                "model": self.model_name or "gpt-3.5-turbo"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"OpenAI连接失败: {str(e)}"
            }

class OllamaProvider(AIProvider):
    """Ollama本地提供者"""
    
    async def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """生成文本"""
        try:
            data = {
                "model": self.model_name or "llama2",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=data,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                else:
                    raise Exception(f"Ollama API错误: {response.status_code}")
        
        except Exception as e:
            raise Exception(f"Ollama文本生成失败: {str(e)}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/version", timeout=5.0)
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Ollama连接成功",
                        "version": response.json().get("version")
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Ollama连接失败: {response.status_code}"
                    }
        except Exception as e:
            return {
                "success": False,
                "message": f"Ollama连接失败: {str(e)}"
            }

# 提供者工厂
class AIProviderFactory:
    """AI提供者工厂"""
    
    _providers = {
        "openai": OpenAIProvider,
        "ollama": OllamaProvider
    }
    
    @classmethod
    def create_provider(cls, provider_name: str, config: Dict[str, Any]) -> AIProvider:
        """创建AI提供者实例"""
        if provider_name not in cls._providers:
            raise ValueError(f"不支持的AI提供者: {provider_name}")
        
        provider_class = cls._providers[provider_name]
        return provider_class(config)
    
    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """获取支持的提供者列表"""
        return list(cls._providers.keys())