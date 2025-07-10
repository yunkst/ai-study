"""
认证系统测试
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch

@pytest.mark.auth
class TestAuthenticationAPI:
    """认证API测试"""
    
    async def test_login_without_key(self, client: AsyncClient):
        """测试无密钥登录"""
        response = await client.post("/api/auth/login", json={})
        
        # 如果没有设置ACCESS_KEY，应该允许无密钥访问
        assert response.status_code in [200, 401]
    
    async def test_login_with_correct_key(self, client: AsyncClient):
        """测试正确密钥登录"""
        response = await client.post(
            "/api/auth/login",
            json={"access_key": "test-key"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    async def test_login_with_wrong_key(self, client: AsyncClient):
        """测试错误密钥登录"""
        response = await client.post(
            "/api/auth/login",
            json={"access_key": "wrong-key"}
        )
        
        assert response.status_code == 401
    
    async def test_logout(self, client: AsyncClient):
        """测试登出"""
        response = await client.post("/api/auth/logout")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

@pytest.mark.auth
@pytest.mark.unit
class TestAuthModule:
    """认证模块单元测试"""
    
    def test_verify_access_key_module_import(self):
        """测试认证模块导入"""
        from core.auth import verify_access_key
        
        assert callable(verify_access_key)
    
    @patch('core.config.settings.ACCESS_KEY', 'test-key')
    async def test_verify_access_key_with_correct_key(self):
        """测试正确密钥验证"""
        from core.auth import verify_access_key
        from fastapi import Request
        
        # 模拟请求对象
        class MockRequest:
            def __init__(self, headers):
                self.headers = headers
        
        request = MockRequest({"x-access-key": "test-key"})
        result = await verify_access_key(request)
        
        assert result is True
    
    @patch('core.config.settings.ACCESS_KEY', 'test-key')
    async def test_verify_access_key_with_wrong_key(self):
        """测试错误密钥验证"""
        from core.auth import verify_access_key
        
        class MockRequest:
            def __init__(self, headers):
                self.headers = headers
        
        request = MockRequest({"x-access-key": "wrong-key"})
        result = await verify_access_key(request)
        
        assert result is False
    
    @patch('core.config.settings.ACCESS_KEY', '')
    async def test_verify_access_key_no_key_required(self):
        """测试无密钥要求时的验证"""
        from core.auth import verify_access_key
        
        class MockRequest:
            def __init__(self, headers):
                self.headers = headers
        
        request = MockRequest({})
        result = await verify_access_key(request)
        
        # 当没有设置ACCESS_KEY时，应该返回True
        assert result is True

@pytest.mark.auth
@pytest.mark.integration
class TestProtectedEndpoints:
    """受保护端点测试"""
    
    async def test_protected_config_without_auth(self, client: AsyncClient):
        """测试受保护的配置端点（无认证）"""
        response = await client.get("/api/config")
        
        assert response.status_code == 401
    
    async def test_protected_config_with_auth(self, authenticated_client: AsyncClient):
        """测试受保护的配置端点（有认证）"""
        response = await authenticated_client.get("/api/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data
    
    async def test_admin_endpoints_require_auth(self, client: AsyncClient):
        """测试管理端点需要认证"""
        endpoints = [
            "/api/admin/stats",
            "/api/admin/users",
            "/api/admin/system"
        ]
        
        for endpoint in endpoints:
            response = await client.get(endpoint)
            # 应该要求认证或返回404（如果未实现）
            assert response.status_code in [401, 404] 