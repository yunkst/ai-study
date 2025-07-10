"""
认证相关API路由
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from core.auth import verify_access_key, get_client_info

router = APIRouter()

class AuthRequest(BaseModel):
    access_key: str

class AuthResponse(BaseModel):
    valid: bool
    message: str
    client_info: dict

@router.post("/verify", response_model=AuthResponse)
async def verify_auth(request: Request, auth_data: AuthRequest):
    """验证访问密钥"""
    # 临时设置密钥到请求头
    request._headers = request.headers.mutablecopy()
    request._headers["x-access-key"] = auth_data.access_key
    
    is_valid = await verify_access_key(request)
    client_info = get_client_info(request)
    
    return AuthResponse(
        valid=is_valid,
        message="访问密钥有效" if is_valid else "访问密钥无效",
        client_info=client_info
    )

@router.get("/status")
async def auth_status(request: Request):
    """获取认证状态"""
    is_valid = await verify_access_key(request)
    client_info = get_client_info(request)
    
    return {
        "authenticated": is_valid,
        "requires_key": bool(request.app.state.settings.ACCESS_KEY) if hasattr(request.app.state, 'settings') else False,
        "client_info": client_info
    } 