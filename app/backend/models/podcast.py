"""
播客数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum, Float
from sqlalchemy.sql import func
from core.database import Base
import enum

class PodcastStatus(enum.Enum):
    GENERATING = "generating"  # 生成中
    READY = "ready"           # 就绪
    ERROR = "error"           # 错误

class PodcastStyle(enum.Enum):
    CONVERSATION = "conversation"  # 对话
    LECTURE = "lecture"           # 讲座
    QA = "qa"                     # 问答

class Podcast(Base):
    __tablename__ = "podcasts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # 内容信息
    topics = Column(JSON, nullable=False)  # 主题列表
    knowledge_points = Column(JSON, nullable=True)  # 知识点
    style = Column(Enum(PodcastStyle), default=PodcastStyle.CONVERSATION)
    
    # 文件信息
    script_content = Column(Text, nullable=True)  # 脚本内容
    audio_file_path = Column(String(500), nullable=True)  # 音频文件路径
    duration_seconds = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    
    # 状态
    status = Column(Enum(PodcastStatus), default=PodcastStatus.GENERATING)
    error_message = Column(Text, nullable=True)
    
    # 生成任务信息
    task_id = Column(String(100), nullable=True)
    generation_progress = Column(Float, default=0.0)  # 0.0 - 1.0
    
    # 统计信息
    listen_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Podcast(id={self.id}, title='{self.title}', status={self.status.value})>" 