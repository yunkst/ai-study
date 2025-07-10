"""
用户数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.sql import func
from core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(255), unique=True, index=True)  # 设备标识
    nickname = Column(String(100), default="学习者")
    
    # 学习统计
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    total_study_time = Column(Integer, default=0)  # 分钟
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, nickname='{self.nickname}')>" 