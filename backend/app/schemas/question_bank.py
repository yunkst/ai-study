"""题库相关的数据模型定义

包含题库相关的Pydantic模型。"""
from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from .question import Subject


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
    subject_id: int | None = None
    file_name: str
    total_questions: int
    imported_questions: int
    question_count: int = 0  # 实际题目数量
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    subject: Optional["Subject"] = None

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
    answer_type: int = 1
    option: list[str] | None = None
    answer: list[str]
    analysis: str | None = None
    raw_data: dict[str, Any] | None = None
    crawl_time: float | None = None
    # 新增字段以匹配服务中的使用
    title: str = ""
    content: str = ""
    options: dict[str, str] | None = None
    correct_answer: str = ""
    explanation: str = ""
    difficulty: str = "medium"
    tags: str = ""
    show_type_name: str = ""


# 在模块加载完成后重建模型以解决前向引用问题
def rebuild_models() -> None:
    """重建所有模型以解决前向引用问题"""
    # 导入Subject类型以解决前向引用
    from .question import Subject  # noqa: F401
    QuestionBank.model_rebuild()


# 注意：不在模块加载时自动重建模型，避免循环导入问题
# 如果需要重建模型，请在应用启动后手动调用 rebuild_models()