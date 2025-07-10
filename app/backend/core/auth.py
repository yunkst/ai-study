"""
简单访问控制认证
"""

from typing import Optional
from fastapi import Request, HTTPException, status
from .config import settings


async def verify_access_key(request: Request) -> bool:
    """验证访问密钥"""
    # 如果没有设置访问密钥，则允许访问
    if not settings.ACCESS_KEY:
        return True
    
    # 从请求头获取密钥
    access_key = request.headers.get("X-Access-Key")
    if not access_key:
        # 从查询参数获取密钥
        access_key = request.query_params.get("access_key")
    
    return access_key == settings.ACCESS_KEY


async def require_access_key(request: Request):
    """要求访问密钥的依赖函数"""
    if not await verify_access_key(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要有效的访问密钥",
            headers={"X-Error": "INVALID_ACCESS_KEY"}
        )


def get_client_info(request: Request) -> dict:
    """获取客户端信息"""
    user_agent = request.headers.get("user-agent", "")
    
    # 简单的设备类型检测
    device_type = "desktop"
    if any(mobile in user_agent.lower() for mobile in ["mobile", "android", "iphone", "ipad"]):
        device_type = "mobile"
    
    return {
        "ip": request.client.host if request.client else "unknown",
        "user_agent": user_agent,
        "device_type": device_type
    } 