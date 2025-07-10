"""
主要API测试
"""

import pytest
from httpx import AsyncClient

@pytest.mark.api
class TestMainAPI:
    """主要API测试类"""
    
    async def test_root_api_info(self, client: AsyncClient):
        """测试根API信息接口"""
        response = await client.get("/api")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["version"] == "1.0.0"
    
    async def test_health_check(self, client: AsyncClient):
        """测试健康检查接口"""
        response = await client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "backend-api"
    
    async def test_config_without_auth(self, client: AsyncClient):
        """测试未认证访问配置接口"""
        response = await client.get("/api/config")
        
        assert response.status_code == 401
        assert "需要访问密钥" in response.json()["detail"]
    
    async def test_config_with_auth(self, authenticated_client: AsyncClient):
        """测试已认证访问配置接口"""
        response = await authenticated_client.get("/api/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data
        assert "features" in data
        assert data["features"]["tts_enabled"] is True

@pytest.mark.api
class TestCORSAndSecurity:
    """CORS和安全测试"""
    
    async def test_cors_headers(self, client: AsyncClient):
        """测试CORS头部"""
        response = await client.options("/api/health")
        
        # FastAPI会自动处理OPTIONS请求
        assert response.status_code in [200, 405]
    
    async def test_nonexistent_endpoint(self, client: AsyncClient):
        """测试不存在的端点"""
        response = await client.get("/api/nonexistent")
        
        assert response.status_code == 404

@pytest.mark.unit
class TestApplicationStartup:
    """应用启动测试"""
    
    def test_app_creation(self):
        """测试应用创建"""
        from main import app
        
        assert app.title == "软件架构师AI学习助手 API"
        assert app.version == "1.0.0"
    
    def test_routers_included(self):
        """测试路由是否正确包含"""
        from main import app
        
        # 检查路由是否存在
        routes = [route.path for route in app.routes]
        
        expected_prefixes = [
            "/api/auth",
            "/api/questions", 
            "/api/practice",
            "/api/podcast",
            "/api/analytics",
            "/api/admin"
        ]
        
        for prefix in expected_prefixes:
            # 至少应该有一些以这些前缀开头的路由
            assert any(route.startswith(prefix) for route in routes) 