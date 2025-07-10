"""
后台任务调度器
"""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

# 全局调度器实例
scheduler = None

def start_scheduler():
    """启动任务调度器"""
    global scheduler
    
    if scheduler is not None:
        return
    
    # 配置调度器
    jobstores = {
        'default': MemoryJobStore()
    }
    executors = {
        'default': AsyncIOExecutor()
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 3
    }
    
    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults
    )
    
    # 添加定时任务
    add_scheduled_jobs()
    
    # 启动调度器
    scheduler.start()
    print("✅ 任务调度器启动完成")

def add_scheduled_jobs():
    """添加定时任务"""
    from services.ai_service import generate_daily_podcast
    from services.analytics_service import analyze_user_progress
    
    # 每天晚上生成播客（示例）
    scheduler.add_job(
        generate_daily_podcast,
        'cron',
        hour=20,  # 晚上8点
        minute=0,
        id='daily_podcast_generation',
        replace_existing=True
    )
    
    # 每小时分析用户学习进度（示例）
    scheduler.add_job(
        analyze_user_progress,
        'interval',
        hours=1,
        id='hourly_analytics',
        replace_existing=True
    )
    
    print("✅ 定时任务添加完成")

def stop_scheduler():
    """停止调度器"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None

def get_scheduler():
    """获取调度器实例"""
    return scheduler 