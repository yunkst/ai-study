"""
练习数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base

class PracticeSession(Base):
    __tablename__ = "practice_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 会话信息
    question_ids = Column(JSON, nullable=False)  # 题目ID列表
    total_questions = Column(Integer, nullable=False)
    
    # 时间记录
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # 成绩统计
    score = Column(Float, nullable=True)
    correct_count = Column(Integer, default=0)
    
    # 关联
    user = relationship("User")
    
    def __repr__(self):
        return f"<PracticeSession(id={self.id}, user_id={self.user_id})>"

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("practice_sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    
    # 答案内容
    user_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    
    # 答题时间
    time_spent_seconds = Column(Integer, nullable=False)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联
    session = relationship("PracticeSession")
    question = relationship("Question")
    
    def __repr__(self):
        return f"<Answer(id={self.id}, question_id={self.question_id}, correct={self.is_correct})>" 