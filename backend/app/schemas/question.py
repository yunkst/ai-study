"""题目相关的数据模型定义

包含题目、选项、科目等相关的Pydantic模型。
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SubjectBase(BaseModel):
    name: str
    description: str | None = None

class SubjectCreate(SubjectBase):
    pass

class Subject(SubjectBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    title: str
    content: str
    question_type: str
    options: dict[str, Any] | None = None
    correct_answer: str
    explanation: str | None = None
    difficulty: int = 1
    tags: list[str] | None = None

class QuestionCreate(QuestionBase):
    subject_id: int

class QuestionUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    question_type: str | None = None
    options: dict[str, Any] | None = None
    correct_answer: str | None = None
    explanation: str | None = None
    difficulty: int | None = None
    tags: list[str] | None = None

class Question(QuestionBase):
    id: int
    subject_id: int
    created_at: datetime
    updated_at: datetime | None = None
    subject: Subject

    class Config:
        from_attributes = True

class QuestionForApp(BaseModel):
    """用于APP的题目格式（不包含正确答案）"""
    id: int
    subject_id: int
    title: str
    content: str
    question_type: str
    options: dict[str, Any] | None = None
    difficulty: int
    tags: list[str] | None = None
    subject: Subject

    class Config:
        from_attributes = True

class UserAnswerBase(BaseModel):
    question_id: int
    user_answer: str
    time_spent: int | None = None

class UserAnswerCreate(UserAnswerBase):
    pass

class UserAnswer(UserAnswerBase):
    id: int
    user_id: int
    is_correct: bool | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class AnswerResult(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: str | None = None
    user_answer: str
