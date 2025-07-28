"""数据库模型定义

包含所有数据库表的SQLAlchemy模型定义。
"""
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), onupdate=text('now()'))

    # 关系
    study_records = relationship("StudyRecord", back_populates="user")
    user_answers = relationship("UserAnswer", back_populates="user")

class Subject(Base):
    """学科模型"""
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))

    # 关系
    questions = relationship("Question", back_populates="subject")

class Question(Base):
    """题目模型"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    question_bank_id = Column(Integer, ForeignKey("question_banks.id"), nullable=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False)  # single_choice, multiple_choice, essay
    options = Column(JSON)  # 选择题选项
    correct_answer = Column(Text)  # 正确答案
    explanation = Column(Text)  # 解析
    difficulty = Column(Integer, default=1)  # 难度等级 1-5
    tags = Column(JSON)  # 标签
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), onupdate=text('now()'))

    # 关系
    subject = relationship("Subject", back_populates="questions")
    question_bank = relationship("QuestionBank", back_populates="questions")
    user_answers = relationship("UserAnswer", back_populates="question")

class UserAnswer(Base):
    """用户答题记录"""
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean)
    time_spent = Column(Integer)  # 答题用时（秒）
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))

    # 关系
    user = relationship("User", back_populates="user_answers")
    question = relationship("Question", back_populates="user_answers")

class StudyRecord(Base):
    """学习记录"""
    __tablename__ = "study_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    study_date = Column(DateTime(timezone=True), server_default=text('now()'))
    questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    study_time = Column(Integer, default=0)  # 学习时间（分钟）

    # 关系
    user = relationship("User", back_populates="study_records")
    subject = relationship("Subject", backref="study_records")

class QuestionBank(Base):
    """题库模型"""
    __tablename__ = "question_banks"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    file_name = Column(String(255), nullable=False)
    total_questions = Column(Integer, default=0)
    imported_questions = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))
    updated_at = Column(DateTime(timezone=True), onupdate=text('now()'))

    # 关系
    subject = relationship("Subject", backref="question_banks")
    questions = relationship("Question", back_populates="question_bank")

class AIConversation(Base):
    """AI对话记录"""
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"))
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    conversation_type = Column(String(50))  # explanation, hint, discussion
    created_at = Column(DateTime(timezone=True), server_default=text('now()'))

    # 关系
    user = relationship("User", backref="ai_conversations")
    question = relationship("Question", backref="ai_conversations")
