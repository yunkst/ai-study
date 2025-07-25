"""题库相关的数据模型定义

包含题库相关的Pydantic模型。
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class QuestionBankBase(BaseModel):
    name: str
    description: str | None = None

class QuestionBankCreate(QuestionBankBase):
    pass

class QuestionBankUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    error_message: str | None = None

class QuestionBank(QuestionBankBase):
    id: int
    file_name: str
    total_questions: int
    imported_questions: int
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

class QuestionBankImportRequest(BaseModel):
    """题库导入请求"""
    name: str
    description: str | None = None

class QuestionBankImportResponse(BaseModel):
    """题库导入响应"""
    question_bank_id: int
    message: str
    total_questions: int

class QuestionImportItem(BaseModel):
    """单个题目导入项"""
    section_id: str
    section_name: str
    question_id: int
    question_title: str
    question_type: int
    answer_type: int
    option: list[str] | None = None
    answer: list[str]
    analysis: str | None = None
    raw_data: dict[str, Any] | None = None
    crawl_time: float | None = None