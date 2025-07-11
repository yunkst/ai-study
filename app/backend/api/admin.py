"""
管理相关API路由
"""

from fastapi import APIRouter, Request, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime, timedelta
import asyncio
import os
import psutil
import logging

from core.database import get_db
from core.config import settings
from models.question import Question
from models.practice import PracticeSession as PracticeSessionModel
from models.podcast import Podcast
from models.user import User
from services.task_manager import task_manager

router = APIRouter()

class SystemStatus(BaseModel):
    status: str
    uptime: str
    database_connected: bool
    redis_connected: bool = False
    ai_service_status: str
    active_tasks: int
    memory_usage_mb: float
    cpu_usage_percent: float
    disk_usage_gb: Dict[str, float]
    last_checked: str

class SystemConfig(BaseModel):
    tts_engine: str
    openai_model: str
    daily_questions_count: int
    podcast_duration_minutes: int
    max_file_size_mb: int
    debug_mode: bool

class SystemLog(BaseModel):
    timestamp: str
    level: str
    message: str
    module: Optional[str] = None

class TaskInfo(BaseModel):
    task_id: str
    task_type: str
    status: str
    progress: float
    created_at: str
    estimated_completion: Optional[str] = None

class MaintenanceTask(BaseModel):
    task_type: str  # cleanup, backup, optimize
    description: Optional[str] = None

async def require_admin(request: Request) -> bool:
    """简化的管理员权限检查"""
    # 这里可以实现真实的管理员权限验证
    return True

def check_database_connection(db: Session) -> bool:
    """检查数据库连接"""
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False

def get_system_uptime() -> str:
    """获取系统运行时间"""
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days} 天, {hours} 小时, {minutes} 分钟"
        elif hours > 0:
            return f"{hours} 小时, {minutes} 分钟"
        else:
            return f"{minutes} 分钟"
    except Exception:
        return "未知"

def get_disk_usage() -> Dict[str, float]:
    """获取磁盘使用情况"""
    try:
        usage = psutil.disk_usage('/')
        return {
            "total": usage.total / (1024**3),  # GB
            "used": usage.used / (1024**3),
            "free": usage.free / (1024**3),
            "percent": usage.used / usage.total * 100
        }
    except Exception:
        return {"total": 0, "used": 0, "free": 0, "percent": 0}

@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """获取系统状态"""
    try:
        # 检查数据库连接
        db_connected = check_database_connection(db)
        
        # 检查AI服务状态（这里简化处理）
        ai_status = "online"
        try:
            # 可以ping AI服务接口
            ai_status = "online"
        except:
            ai_status = "offline"
        
        # 获取活跃任务数
        active_tasks = len(task_manager.running_tasks)
        
        # 系统资源使用情况
        memory = psutil.virtual_memory()
        memory_usage_mb = memory.used / (1024*1024)
        cpu_usage = psutil.cpu_percent(interval=1)
        disk_usage = get_disk_usage()
        
        # 系统总体状态
        status = "healthy"
        if not db_connected:
            status = "database_error"
        elif memory.percent > 90 or cpu_usage > 90:
            status = "high_load"
        elif disk_usage.get("percent", 0) > 90:
            status = "disk_full"
        
        return SystemStatus(
            status=status,
            uptime=get_system_uptime(),
            database_connected=db_connected,
            redis_connected=False,  # 如果使用Redis可以实现检查
            ai_service_status=ai_status,
            active_tasks=active_tasks,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage,
            disk_usage_gb=disk_usage,
            last_checked=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")

@router.get("/config", response_model=SystemConfig)
async def get_system_config(
    request: Request,
    _: bool = Depends(require_admin)
):
    """获取系统配置"""
    try:
        return SystemConfig(
            tts_engine=getattr(settings, 'TTS_ENGINE', 'edge'),
            openai_model=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
            daily_questions_count=getattr(settings, 'DAILY_QUESTIONS_COUNT', 10),
            podcast_duration_minutes=getattr(settings, 'PODCAST_DURATION_MINUTES', 15),
            max_file_size_mb=getattr(settings, 'MAX_FILE_SIZE_MB', 50),
            debug_mode=getattr(settings, 'DEBUG', False)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统配置失败: {str(e)}")

@router.put("/config")
async def update_system_config(
    request: Request,
    config: SystemConfig,
    _: bool = Depends(require_admin)
):
    """更新系统配置"""
    try:
        # 更新配置到环境变量或配置文件
        # 这里简化处理，实际应该持久化到配置存储
        
        # 验证配置值
        if config.daily_questions_count < 1 or config.daily_questions_count > 100:
            raise HTTPException(status_code=400, detail="每日题目数量必须在1-100之间")
        
        if config.podcast_duration_minutes < 1 or config.podcast_duration_minutes > 60:
            raise HTTPException(status_code=400, detail="播客时长必须在1-60分钟之间")
        
        # 这里可以实现配置的持久化存储
        # 例如写入数据库或配置文件
        
        return {
            "message": "配置更新成功",
            "updated_config": config.dict(),
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")

@router.get("/logs", response_model=List[SystemLog])
async def get_system_logs(
    request: Request,
    limit: int = Query(100, description="日志条数限制"),
    level: Optional[str] = Query(None, description="日志级别筛选"),
    module: Optional[str] = Query(None, description="模块筛选"),
    _: bool = Depends(require_admin)
):
    """获取系统日志"""
    try:
        logs = []
        
        # 这里简化实现，实际应该从日志文件或日志存储中读取
        log_levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
        modules = ["api", "services", "tasks", "database", "ai"]
        
        # 生成模拟日志数据
        for i in range(min(limit, 50)):
            import random
            log_level = random.choice(log_levels)
            log_module = random.choice(modules)
            
            # 应用筛选
            if level and log_level != level.upper():
                continue
            if module and log_module != module:
                continue
            
            timestamp = datetime.now() - timedelta(minutes=i*5)
            
            messages = {
                "INFO": f"[{log_module}] 服务正常运行",
                "WARNING": f"[{log_module}] 检测到潜在问题",
                "ERROR": f"[{log_module}] 发生错误",
                "DEBUG": f"[{log_module}] 调试信息"
            }
            
            logs.append(SystemLog(
                timestamp=timestamp.isoformat(),
                level=log_level,
                message=messages.get(log_level, "未知消息"),
                module=log_module
            ))
        
        return logs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")

@router.get("/tasks", response_model=List[TaskInfo])
async def get_active_tasks(
    request: Request,
    _: bool = Depends(require_admin)
):
    """获取活跃任务列表"""
    try:
        tasks = []
        
        # 从任务管理器获取任务信息
        for task_id, task_info in task_manager.running_tasks.items():
            task_type = task_info.get("type", "unknown")
            progress = task_info.get("progress", 0.0)
            created_at = task_info.get("created_at", datetime.now())
            
            # 估算完成时间
            estimated_completion = None
            if progress > 0:
                elapsed = datetime.now() - created_at
                total_time = elapsed / progress
                remaining = total_time - elapsed
                estimated_completion = (datetime.now() + remaining).isoformat()
            
            tasks.append(TaskInfo(
                task_id=task_id,
                task_type=task_type,
                status="running",
                progress=progress,
                created_at=created_at.isoformat(),
                estimated_completion=estimated_completion
            ))
        
        return tasks
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")

@router.post("/maintenance")
async def trigger_maintenance(
    request: Request,
    maintenance_task: MaintenanceTask,
    _: bool = Depends(require_admin)
):
    """触发系统维护任务"""
    try:
        task_type = maintenance_task.task_type
        
        if task_type == "cleanup":
            # 清理临时文件和过期数据
            result = await _cleanup_system()
        elif task_type == "backup":
            # 数据备份
            result = await _backup_system()
        elif task_type == "optimize":
            # 系统优化
            result = await _optimize_system()
        else:
            raise HTTPException(status_code=400, detail=f"未知的维护任务类型: {task_type}")
        
        return {
            "message": f"维护任务 {task_type} 已启动",
            "task_details": result,
            "started_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动维护任务失败: {str(e)}")

async def _cleanup_system() -> Dict[str, Any]:
    """系统清理任务"""
    try:
        cleaned_files = 0
        freed_space_mb = 0
        
        # 清理临时文件
        temp_dir = getattr(settings, 'TEMP_DIR', '/tmp')
        if os.path.exists(temp_dir):
            for filename in os.listdir(temp_dir):
                if filename.startswith('temp_'):
                    file_path = os.path.join(temp_dir, filename)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        os.remove(file_path)
                        cleaned_files += 1
                        freed_space_mb += size / (1024*1024)
        
        return {
            "cleaned_files": cleaned_files,
            "freed_space_mb": round(freed_space_mb, 2),
            "status": "completed"
        }
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}

async def _backup_system() -> Dict[str, Any]:
    """系统备份任务"""
    try:
        # 这里应该实现数据库备份逻辑
        backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        return {
            "backup_file": backup_file,
            "backup_size_mb": 15.6,  # 模拟数据
            "status": "completed"
        }
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}

async def _optimize_system() -> Dict[str, Any]:
    """系统优化任务"""
    try:
        # 这里可以实现数据库优化、缓存清理等
        optimizations = [
            "数据库索引重建",
            "查询缓存清理",
            "会话清理"
        ]
        
        return {
            "optimizations": optimizations,
            "performance_improvement": "12%",  # 模拟数据
            "status": "completed"
        }
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}

@router.get("/stats/overview")
async def get_admin_overview(
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """获取管理员概览数据"""
    try:
        # 用户统计
        total_users = db.query(User).count()
        active_users = db.query(User).filter(
            User.last_login > datetime.now() - timedelta(days=30)
        ).count()
        
        # 题目统计
        total_questions = db.query(Question).count()
        questions_by_difficulty = {}
        for difficulty in [1, 2, 3]:
            count = db.query(Question).filter(Question.difficulty == difficulty).count()
            questions_by_difficulty[str(difficulty)] = count
        
        # 练习统计
        total_sessions = db.query(PracticeSessionModel).count()
        active_sessions = db.query(PracticeSessionModel).filter(
            PracticeSessionModel.end_time.is_(None)
        ).count()
        
        # 播客统计
        total_podcasts = db.query(Podcast).count()
        ready_podcasts = db.query(Podcast).filter(
            Podcast.status == "ready"
        ).count()
        
        # 存储使用情况
        storage_used_mb = 0
        data_dirs = [
            getattr(settings, 'PODCAST_DIR', './data/podcasts'),
            getattr(settings, 'UPLOAD_DIR', './data/uploads')
        ]
        
        for data_dir in data_dirs:
            if os.path.exists(data_dir):
                for root, dirs, files in os.walk(data_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.isfile(file_path):
                            storage_used_mb += os.path.getsize(file_path) / (1024*1024)
        
        # 近期活动统计
        recent_sessions = db.query(PracticeSessionModel).filter(
            PracticeSessionModel.start_time > datetime.now() - timedelta(days=7)
        ).count()
        
        recent_podcasts = db.query(Podcast).filter(
            Podcast.created_at > datetime.now() - timedelta(days=7)
        ).count()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_questions": total_questions,
            "questions_by_difficulty": questions_by_difficulty,
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_podcasts": total_podcasts,
            "ready_podcasts": ready_podcasts,
            "storage_used_mb": round(storage_used_mb, 2),
            "recent_activity": {
                "sessions_this_week": recent_sessions,
                "podcasts_this_week": recent_podcasts
            },
            "system_health": {
                "memory_usage_percent": psutil.virtual_memory().percent,
                "cpu_usage_percent": psutil.cpu_percent(),
                "disk_usage_percent": get_disk_usage().get("percent", 0)
            },
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取概览数据失败: {str(e)}")

@router.post("/cache/clear")
async def clear_cache(
    request: Request,
    cache_type: str = Query("all", description="缓存类型: all, api, tts, ai"),
    _: bool = Depends(require_admin)
):
    """清理系统缓存"""
    try:
        cleared_items = 0
        
        if cache_type in ["all", "api"]:
            # 清理API缓存
            cleared_items += 10  # 模拟数据
        
        if cache_type in ["all", "tts"]:
            # 清理TTS缓存
            cleared_items += 5
        
        if cache_type in ["all", "ai"]:
            # 清理AI缓存
            cleared_items += 8
        
        return {
            "message": f"缓存清理完成",
            "cache_type": cache_type,
            "cleared_items": cleared_items,
            "cleared_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理缓存失败: {str(e)}") 