"""
题目数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum
from sqlalchemy.sql import func
from core.database import Base
import enum

class QuestionType(enum.Enum):
    CHOICE = "choice"      # 选择题
    CASE = "case"          # 案例分析
    ESSAY = "essay"        # 论文设计

class DifficultyLevel(enum.Enum):
    BASIC = 1       # 基础
    INTERMEDIATE = 2  # 中级
    ADVANCED = 3     # 高级

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_type = Column(Enum(QuestionType), nullable=False)
    content = Column(Text, nullable=False)
    
    # 选择题选项 (JSON格式存储)
    options = Column(JSON, nullable=True)
    
    # 正确答案
    correct_answer = Column(Text, nullable=False)
    
    # 解析说明
    explanation = Column(Text, nullable=True)
    
    # 难度和知识点
    difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.BASIC)
    knowledge_points = Column(JSON, nullable=True)  # 知识点数组
    
    # 统计信息
    total_attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    @property
    def accuracy_rate(self):
        """正确率"""
        if self.total_attempts == 0:
            return 0.0
        return self.correct_attempts / self.total_attempts
    
    def __repr__(self):
        return f"<Question(id={self.id}, type={self.question_type.value})>" 