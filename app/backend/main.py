"""
软件架构师AI学习助手 - 后端API服务
"""

import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.auth import verify_access_key
from core.database import init_db
from core.scheduler import start_scheduler

from api import auth, questions, practice, podcast, analytics, admin

# 创建FastAPI应用
app = FastAPI(
    title="软件架构师AI学习助手 API",
    description="AI驱动的个性化学习系统后端API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 局域网使用，允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(questions.router, prefix="/api/questions", tags=["题库"])
app.include_router(practice.router, prefix="/api/practice", tags=["练习"])
app.include_router(podcast.router, prefix="/api/podcast", tags=["播客"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["分析"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理"])

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    print("🚀 启动软件架构师AI学习助手后端服务...")
    
    # 初始化数据库
    await init_db()
    
    # 启动后台任务调度器
    start_scheduler()
    
    print("✅ 后端服务启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    print("🛑 正在关闭后端服务...")

@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "ok",
        "message": "后端服务运行正常",
        "version": "1.0.0",
        "service": "backend-api"
    }

@app.get("/api/config")
async def get_config(request: Request):
    """获取系统配置信息"""
    # 简单的访问控制
    if not await verify_access_key(request):
        raise HTTPException(status_code=401, detail="需要访问密钥")
    
    return {
        "app_name": settings.APP_NAME,
        "version": "1.0.0",
        "features": {
            "tts_enabled": True,
            "ai_chat_enabled": True,
            "analytics_enabled": True
        }
    }

# 根路径API信息
@app.get("/api")
async def api_info():
    """API信息接口"""
    return {
        "name": "软件架构师AI学习助手 API",
        "version": "1.0.0",
        "description": "AI驱动的个性化学习系统后端API",
        "docs_url": "/docs",
        "health_url": "/api/health"
    }

if __name__ == "__main__":
    # 开发模式启动
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    ) 