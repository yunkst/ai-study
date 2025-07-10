"""
学习分析数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base

class LearningAnalysis(Base):
    __tablename__ = "learning_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 分析周期
    analysis_date = Column(DateTime(timezone=True), server_default=func.now())
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # 整体表现
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    accuracy_rate = Column(Float, default=0.0)
    average_time_per_question = Column(Float, default=0.0)  # 秒
    study_sessions = Column(Integer, default=0)
    total_study_time = Column(Integer, default=0)  # 分钟
    
    # 知识点分析 (JSON格式)
    knowledge_points_analysis = Column(JSON, nullable=True)
    
    # 难度分析 (JSON格式)
    difficulty_analysis = Column(JSON, nullable=True)
    
    # AI生成的建议
    ai_recommendations = Column(Text, nullable=True)
    
    # 薄弱点
    weak_points = Column(JSON, nullable=True)
    
    # 关联
    user = relationship("User")
    
    def __repr__(self):
        return f"<LearningAnalysis(id={self.id}, user_id={self.user_id}, date={self.analysis_date})>"

class StudyPlan(Base):
    __tablename__ = "study_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 计划信息
    plan_title = Column(String(255), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # 目标设置
    daily_questions_target = Column(Integer, default=10)
    daily_study_time_target = Column(Integer, default=45)  # 分钟
    accuracy_target = Column(Float, default=0.8)
    
    # 重点知识点
    focus_topics = Column(JSON, nullable=True)
    
    # 计划详情 (JSON格式)
    plan_details = Column(JSON, nullable=True)
    
    # 执行状态
    is_active = Column(Integer, default=1)  # SQLite兼容的布尔值
    completion_rate = Column(Float, default=0.0)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联
    user = relationship("User")
    
    def __repr__(self):
        return f"<StudyPlan(id={self.id}, title='{self.plan_title}', active={bool(self.is_active)})>" 