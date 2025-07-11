"""
知识库相关数据模型
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Table, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

# 知识点依赖关系关联表
knowledge_dependencies = Table(
    'knowledge_dependencies',
    Base.metadata,
    Column('prerequisite_id', String, ForeignKey('knowledge_points.id'), primary_key=True),
    Column('dependent_id', String, ForeignKey('knowledge_points.id'), primary_key=True)
)

# 学习路径知识点关联表
learning_path_knowledge_points = Table(
    'learning_path_knowledge_points',
    Base.metadata,
    Column('learning_path_id', String, ForeignKey('learning_paths.id'), primary_key=True),
    Column('knowledge_point_id', String, ForeignKey('knowledge_points.id'), primary_key=True),
    Column('sequence_order', Integer),
    Column('is_required', Boolean, default=True)
)

class KnowledgeDomain(Base):
    """知识域模型"""
    __tablename__ = 'knowledge_domains'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    exam_weight = Column(Float, default=0.0)  # 考试权重
    sort_order = Column(Integer, default=0)
    color = Column(String(20), default='#409EFF')  # 显示颜色
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    knowledge_points = relationship('KnowledgePoint', back_populates='domain', cascade='all, delete-orphan')

class KnowledgePoint(Base):
    """知识点模型"""
    __tablename__ = 'knowledge_points'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    content = Column(Text)  # 详细内容
    difficulty_level = Column(Integer, default=1)  # 1-5难度等级
    exam_weight = Column(Float, default=0.0)  # 考试权重
    estimated_study_hours = Column(Float, default=1.0)  # 预估学习时间
    learning_objectives = Column(JSON)  # 学习目标
    keywords = Column(JSON)  # 关键词列表
    references = Column(JSON)  # 参考资料
    examples = Column(Text)  # 示例
    exercises = Column(JSON)  # 练习题
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键
    domain_id = Column(String, ForeignKey('knowledge_domains.id'))
    
    # 关系
    domain = relationship('KnowledgeDomain', back_populates='knowledge_points')
    skill_points = relationship('SkillPoint', back_populates='knowledge_point', cascade='all, delete-orphan')
    
    # 自引用多对多关系
    prerequisites = relationship(
        'KnowledgePoint',
        secondary=knowledge_dependencies,
        primaryjoin=id == knowledge_dependencies.c.dependent_id,
        secondaryjoin=id == knowledge_dependencies.c.prerequisite_id,
        back_populates='dependents'
    )
    dependents = relationship(
        'KnowledgePoint',
        secondary=knowledge_dependencies,
        primaryjoin=id == knowledge_dependencies.c.prerequisite_id,
        secondaryjoin=id == knowledge_dependencies.c.dependent_id,
        back_populates='prerequisites'
    )
    
    # 学习进度关系
    user_progress = relationship('UserKnowledgeProgress', back_populates='knowledge_point')

class SkillPoint(Base):
    """技能点模型"""
    __tablename__ = 'skill_points'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    skill_type = Column(String(50))  # concept, technique, application
    mastery_criteria = Column(Text)  # 掌握标准
    practice_methods = Column(JSON)  # 练习方法
    assessment_questions = Column(JSON)  # 评估问题
    difficulty_level = Column(Integer, default=1)
    estimated_practice_hours = Column(Float, default=0.5)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键
    knowledge_point_id = Column(String, ForeignKey('knowledge_points.id'))
    
    # 关系
    knowledge_point = relationship('KnowledgePoint', back_populates='skill_points')

class UserKnowledgeProgress(Base):
    """用户知识点学习进度"""
    __tablename__ = 'user_knowledge_progress'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)  # 用户ID
    knowledge_point_id = Column(String, ForeignKey('knowledge_points.id'))
    mastery_level = Column(Float, default=0.0)  # 掌握程度 0.0-1.0
    study_time_minutes = Column(Integer, default=0)  # 学习时间（分钟）
    last_reviewed_at = Column(DateTime)  # 最后复习时间
    review_count = Column(Integer, default=0)  # 复习次数
    correct_answers = Column(Integer, default=0)  # 正确答题数
    total_answers = Column(Integer, default=0)  # 总答题数
    notes = Column(Text)  # 学习笔记
    is_bookmarked = Column(Boolean, default=False)  # 是否收藏
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    knowledge_point = relationship('KnowledgePoint', back_populates='user_progress')

class LearningPath(Base):
    """学习路径模型"""
    __tablename__ = 'learning_paths'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    target_exam = Column(String(100))  # 目标考试
    difficulty_level = Column(Integer, default=1)  # 路径难度
    estimated_total_hours = Column(Float, default=0.0)  # 预估总时间
    prerequisites_description = Column(Text)  # 前置要求描述
    learning_objectives = Column(JSON)  # 学习目标
    is_public = Column(Boolean, default=True)  # 是否公开
    is_active = Column(Boolean, default=True)
    created_by = Column(String)  # 创建者
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    knowledge_points = relationship(
        'KnowledgePoint',
        secondary=learning_path_knowledge_points,
        back_populates='learning_paths'
    )
    user_plans = relationship('UserLearningPlan', back_populates='learning_path')

# 反向关系
KnowledgePoint.learning_paths = relationship(
    'LearningPath',
    secondary=learning_path_knowledge_points,
    back_populates='knowledge_points'
)

class UserLearningPlan(Base):
    """用户学习计划"""
    __tablename__ = 'user_learning_plans'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    learning_path_id = Column(String, ForeignKey('learning_paths.id'))
    plan_name = Column(String(200))
    start_date = Column(DateTime)
    target_completion_date = Column(DateTime)
    daily_study_hours = Column(Float, default=2.0)
    current_knowledge_point_id = Column(String, ForeignKey('knowledge_points.id'))
    completion_percentage = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON)  # 个性化设置
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    learning_path = relationship('LearningPath', back_populates='user_plans')
    current_knowledge_point = relationship('KnowledgePoint')
    daily_plans = relationship('DailyLearningPlan', back_populates='user_plan')

class DailyLearningPlan(Base):
    """每日学习计划"""
    __tablename__ = 'daily_learning_plans'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_plan_id = Column(String, ForeignKey('user_learning_plans.id'))
    plan_date = Column(DateTime, nullable=False)
    planned_knowledge_points = Column(JSON)  # 计划学习的知识点
    planned_study_hours = Column(Float, default=2.0)
    actual_study_hours = Column(Float, default=0.0)
    completed_knowledge_points = Column(JSON)  # 完成的知识点
    notes = Column(Text)
    mood_rating = Column(Integer)  # 学习心情评分 1-5
    difficulty_rating = Column(Integer)  # 难度评分 1-5
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user_plan = relationship('UserLearningPlan', back_populates='daily_plans')

class LearningRecommendation(Base):
    """学习推荐记录"""
    __tablename__ = 'learning_recommendations'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    knowledge_point_id = Column(String, ForeignKey('knowledge_points.id'))
    recommendation_type = Column(String(50))  # review, learn, practice
    priority_score = Column(Float, default=0.0)
    reason = Column(Text)  # 推荐原因
    recommended_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_accepted = Column(Boolean)
    is_active = Column(Boolean, default=True)
    
    # 关系
    knowledge_point = relationship('KnowledgePoint')

class DocumentChunk(Base):
    """RAG文档分块存储"""
    __tablename__ = 'document_chunks'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_file = Column(String(500), nullable=False)
    file_hash = Column(String(64))  # 文件哈希
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(50))  # text, code, table, image
    chapter = Column(String(200))  # 章节
    section = Column(String(200))  # 小节
    metadata = Column(JSON)  # 元数据
    embedding_model = Column(String(100))
    embedding_vector = Column(JSON)  # 存储向量（简化版，实际可用专门的向量数据库）
    chunk_length = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ImportTask(Base):
    """知识库导入任务"""
    __tablename__ = 'import_tasks'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_name = Column(String(200), nullable=False)
    task_type = Column(String(50))  # scan, upload, rag
    source_path = Column(String(500))
    parameters = Column(JSON)  # 导入参数
    status = Column(String(20), default='pending')  # pending, running, completed, failed
    progress = Column(Float, default=0.0)
    message = Column(Text)
    result_summary = Column(JSON)  # 导入结果摘要
    error_details = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemConfig(Base):
    """系统配置"""
    __tablename__ = 'system_configs'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    config_key = Column(String(100), nullable=False, unique=True)
    config_value = Column(JSON)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 