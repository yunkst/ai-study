"""AI相关的数据模型定义

包含AI对话、消息等相关的Pydantic模型。
"""
from datetime import datetime

from pydantic import BaseModel


class AIMessageBase(BaseModel):
    user_message: str
    conversation_type: str = "discussion"  # explanation, hint, discussion
    question_id: int | None = None

class AIMessageCreate(AIMessageBase):
    pass

class AIMessage(AIMessageBase):
    id: int
    user_id: int
    ai_response: str
    created_at: datetime

    class Config:
        from_attributes = True

class AIStreamRequest(BaseModel):
    message: str
    question_id: int | None = None
    conversation_type: str = "discussion"
    context: str | None = None

class AIStreamResponse(BaseModel):
    content: str
    is_complete: bool = False

class StudyRecordBase(BaseModel):
    subject_id: int | None = None
    questions_answered: int = 0
    correct_answers: int = 0
    study_time: int = 0

class StudyRecordCreate(StudyRecordBase):
    pass

class StudyRecord(StudyRecordBase):
    id: int
    user_id: int
    study_date: datetime

    class Config:
        from_attributes = True

class StudyStats(BaseModel):
    total_questions: int
    correct_answers: int
    accuracy_rate: float
    total_study_time: int
    subjects_studied: list[str]
    recent_records: list[StudyRecord]
