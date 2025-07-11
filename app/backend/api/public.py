from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any, Optional
import os
import re

from services.task_manager import get_task_manager

router = APIRouter()


@router.get("/tasks")
async def get_tasks(limit: int = Query(100, description="返回任务数量")):
    """获取任务列表（无鉴权）"""
    tasks = get_task_manager().list_tasks(limit=limit)
    result = []
    for t in tasks:
        result.append({
            "id": t.id,
            "name": t.name,
            "status": t.status.value,
            "last_run": t.completed_at.isoformat() if t.completed_at else "—",
            "next_run": "—"
        })
    return result


@router.get("/logs")
async def get_logs(limit: int = Query(100, description="返回日志条数")):
    """读取后台日志文件并返回最近若干条"""
    log_file = os.getenv("LOG_FILE_PATH", "app.log")
    if not os.path.exists(log_file):
        return []

    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-limit:]

        pattern = re.compile(r"^(?P<timestamp>[^ ]+ [^ ]+) - (?P<logger>[^ ]+) - (?P<level>[^ ]+) - (?P<message>.*)$")
        logs: List[Dict[str, Any]] = []
        for line in lines:
            match = pattern.match(line.strip())
            if match:
                logs.append({
                    "timestamp": match.group("timestamp"),
                    "level": match.group("level"),
                    "message": match.group("message")
                })
        # 逆序，最新的日志在最上方
        return list(reversed(logs))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取日志失败: {e}") 