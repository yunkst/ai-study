"""
认证相关API路由
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from core.auth import get_client_info

router = APIRouter()

@router.get("/status")
async def auth_status(request: Request):
    """获取认证状态 - 简化为始终返回管理员"""
    client_info = get_client_info(request)
    
    return {
        "authenticated": True,
        "user": {
            "id": "default_user",
            "username": "admin",
            "email": "admin@example.com",
            "role": "admin",
            "is_active": True,
        },
        "client_info": client_info,
    } 