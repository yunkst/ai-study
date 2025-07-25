"""API v1路由配置

配置所有v1版本的API路由。
"""
from fastapi import APIRouter

from app.api.v1.endpoints import ai, auth, questions, question_banks

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(questions.router, prefix="/questions", tags=["questions"])
api_router.include_router(question_banks.router, prefix="/question-banks", tags=["question-banks"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
