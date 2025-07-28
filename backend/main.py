import logging
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.services.migration_service import migration_service
from app.schemas.question_bank import rebuild_models

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 启动时执行数据库迁移检查
try:
    logger.info("Starting database migration check...")
    if not migration_service.startup_migration_check():
        logger.error("Database migration check failed, exiting...")
        sys.exit(1)
    logger.info("Database migration check completed successfully")
    
    # 重建Pydantic模型以解决前向引用问题
    logger.info("Rebuilding Pydantic models...")
    rebuild_models()
    logger.info("Pydantic models rebuilt successfully")
except Exception as e:
    logger.error(f"Database migration check failed with exception: {e}")
    sys.exit(1)

app = FastAPI(
    title="AI Study Platform API",
    description="AI驱动的学习平台后端API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "AI Study Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
