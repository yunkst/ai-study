"""
学习路径规划数据模型
"""

from sqlalchemy import Column, Integer, String, Text, Float, JSON, ForeignKey, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base
import enum

class LearningGoal(enum.Enum):
    BASIC_PASS = "basic_pass"           # 基础过关
    HIGH_SCORE = "high_score"           # 高分通过
    COMPREHENSIVE = "comprehensive"     # 全面掌握
    QUICK_REVIEW = "quick_review"       # 快速复习

class PathStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"

class LearningPath(Base):
    """学习路径模板"""
    __tablename__ = "learning_paths"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # 路径类型和目标
    learning_goal = Column(Enum(LearningGoal), nullable=False)
    
    # 预估完成时间（天）
    estimated_days = Column(Integer, default=30)
    
    # 难度级别 (1-5)
    difficulty_level = Column(Integer, default=1)
    
    # 知识点序列（按学习顺序）
    knowledge_point_sequence = Column(JSON, nullable=False)  # [{"kp_id": 1, "order": 1, "weight": 0.1}, ...]
    
    # 学习阶段划分
    learning_stages = Column(JSON, nullable=True)  # [{"name": "基础阶段", "kp_ids": [1,2,3], "target_days": 10}, ...]
    
    # 是否为默认路径
    is_default = Column(Boolean, default=False)
    
    # 是否启用
    is_active = Column(Boolean, default=True)
    
    # 创建者
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    creator = relationship("User", foreign_keys=[created_by])
    user_plans = relationship("UserLearningPlan", back_populates="learning_path")
    
    def __repr__(self):
        return f"<LearningPath(id={self.id}, name='{self.name}', goal={self.learning_goal.value})>"

class UserLearningPlan(Base):
    """用户个人学习计划"""
    __tablename__ = "user_learning_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    
    # 计划信息
    plan_name = Column(String(200), nullable=False)
    target_exam_date = Column(DateTime(timezone=True), nullable=True)
    
    # 状态
    status = Column(Enum(PathStatus), default=PathStatus.NOT_STARTED)
    
    # 进度信息
    current_stage = Column(Integer, default=0)  # 当前学习阶段
    overall_progress = Column(Float, default=0.0)  # 总体进度 (0-1)
    
    # 个性化调整
    daily_study_hours = Column(Float, default=2.0)  # 每日学习时间
    preferred_difficulty = Column(Integer, default=2)  # 偏好难度
    
    # 自定义知识点序列（覆盖模板）
    custom_sequence = Column(JSON, nullable=True)
    
    # 时间记录
    start_date = Column(DateTime(timezone=True), nullable=True)
    expected_completion_date = Column(DateTime(timezone=True), nullable=True)
    actual_completion_date = Column(DateTime(timezone=True), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    user = relationship("User")
    learning_path = relationship("LearningPath", back_populates="user_plans")
    daily_plans = relationship("DailyLearningPlan", back_populates="user_plan")
    
    def __repr__(self):
        return f"<UserLearningPlan(id={self.id}, user_id={self.user_id}, status={self.status.value})>"

class DailyLearningPlan(Base):
    """每日学习计划"""
    __tablename__ = "daily_learning_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_plan_id = Column(Integer, ForeignKey("user_learning_plans.id"), nullable=False)
    
    # 日期
    plan_date = Column(DateTime(timezone=True), nullable=False)
    
    # 计划内容
    planned_knowledge_points = Column(JSON, nullable=False)  # [{"kp_id": 1, "target_mastery": 0.8}, ...]
    planned_study_minutes = Column(Integer, default=120)
    
    # 完成情况
    actual_study_minutes = Column(Integer, default=0)
    completed_knowledge_points = Column(JSON, nullable=True)  # [{"kp_id": 1, "achieved_mastery": 0.7}, ...]
    
    # 状态
    is_completed = Column(Boolean, default=False)
    completion_rate = Column(Float, default=0.0)  # 完成率 (0-1)
    
    # 反馈和调整
    difficulty_feedback = Column(Integer, nullable=True)  # 1-5, 难度反馈
    notes = Column(Text, nullable=True)  # 学习笔记
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    user_plan = relationship("UserLearningPlan", back_populates="daily_plans")
    
    def __repr__(self):
        return f"<DailyLearningPlan(id={self.id}, date={self.plan_date}, completed={self.is_completed})>"

class LearningRecommendation(Base):
    """学习推荐记录"""
    __tablename__ = "learning_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 推荐类型
    recommendation_type = Column(String(50), nullable=False)  # next_topic, review, practice, etc.
    
    # 推荐内容
    recommended_knowledge_points = Column(JSON, nullable=False)  # [{"kp_id": 1, "reason": "weak_area", "priority": 0.9}, ...]
    
    # 推荐理由和算法
    algorithm_version = Column(String(20), default="v1.0")
    reasoning = Column(JSON, nullable=True)  # 推荐算法的决策过程
    
    # 用户反馈
    user_feedback = Column(JSON, nullable=True)  # {"usefulness": 4, "followed": true}
    
    # 推荐有效性
    recommendation_score = Column(Float, default=0.5)  # 推荐质量分数
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # 推荐过期时间
    
    # 关联关系
    user = relationship("User")
    
    def __repr__(self):
        return f"<LearningRecommendation(id={self.id}, user_id={self.user_id}, type={self.recommendation_type})>" 