"""
学习分析相关API路由
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from services.analytics_service import analytics_service
from services.task_manager import task_manager

router = APIRouter()

class LearningStats(BaseModel):
    total_questions: int
    correct_rate: float
    weak_points: List[str]
    strong_points: List[str]
    study_time_hours: float
    last_study_date: str
    difficulty_breakdown: Dict[str, float]

class ProgressReport(BaseModel):
    period: str  # daily, weekly, monthly
    knowledge_points: Dict[str, float]  # 知识点掌握度
    difficulty_progress: Dict[str, float]  # 各难度掌握情况
    recommendations: List[str]
    trends: Dict[str, str]
    daily_stats: Optional[List[Dict[str, Any]]] = None

class WeakPoint(BaseModel):
    topic: str
    mastery: float
    questions_count: int
    priority: str
    recommendation: str

async def get_user_id(request: Request) -> str:
    """从请求中获取用户ID，这里简化为默认用户"""
    return "default"

@router.get("/stats", response_model=LearningStats)
async def get_learning_stats(
    request: Request,
    user_id: str = Depends(get_user_id)
):
    """获取学习统计数据"""
    try:
        performance = await analytics_service.analyze_user_performance(user_id)
        weak_points_data = await analytics_service.identify_weak_points(user_id)
        
        if not performance:
            raise HTTPException(status_code=404, detail="用户学习数据未找到")
        
        # 计算强项（掌握度>80%的知识点）
        knowledge_points = performance.get("knowledge_points", {})
        strong_points = [
            topic for topic, data in knowledge_points.items() 
            if data.get("mastery", 0) > 0.8
        ]
        
        weak_points = [wp["topic"] for wp in weak_points_data]
        
        # 计算难度分布
        difficulty_analysis = performance.get("difficulty_analysis", {})
        difficulty_breakdown = {
            level: data.get("accuracy", 0) 
            for level, data in difficulty_analysis.items()
        }
        
        return LearningStats(
            total_questions=performance.get("total_questions", 0),
            correct_rate=performance.get("accuracy_rate", 0.0),
            weak_points=weak_points,
            strong_points=strong_points,
            study_time_hours=performance.get("total_study_time", 0) / 60.0,  # 转换为小时
            last_study_date=performance.get("analysis_date", datetime.now().isoformat()),
            difficulty_breakdown=difficulty_breakdown
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学习统计失败: {str(e)}")

@router.get("/progress", response_model=ProgressReport)
async def get_progress_report(
    request: Request,
    period: str = "weekly",
    user_id: str = Depends(get_user_id)
):
    """获取学习进度报告"""
    try:
        # 根据时间周期确定天数
        days_map = {"daily": 1, "weekly": 7, "monthly": 30}
        days = days_map.get(period, 7)
        
        progress_data = await analytics_service.track_learning_progress(user_id, days)
        performance = await analytics_service.analyze_user_performance(user_id)
        study_plan = await analytics_service.generate_study_plan(user_id)
        
        if not progress_data:
            raise HTTPException(status_code=404, detail="进度数据未找到")
        
        # 构建知识点掌握度
        knowledge_points = performance.get("knowledge_points", {})
        knowledge_mastery = {
            topic: data.get("mastery", 0) 
            for topic, data in knowledge_points.items()
        }
        
        # 构建难度进度
        difficulty_analysis = performance.get("difficulty_analysis", {})
        difficulty_progress = {
            level: data.get("accuracy", 0) 
            for level, data in difficulty_analysis.items()
        }
        
        return ProgressReport(
            period=period,
            knowledge_points=knowledge_mastery,
            difficulty_progress=difficulty_progress,
            recommendations=study_plan.get("recommendations", []),
            trends=progress_data.get("trends", {}),
            daily_stats=progress_data.get("daily_stats", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取进度报告失败: {str(e)}")

@router.get("/weak-points", response_model=List[WeakPoint])
async def get_weak_points(
    request: Request,
    user_id: str = Depends(get_user_id)
):
    """获取薄弱知识点详情"""
    try:
        weak_points_data = await analytics_service.identify_weak_points(user_id)
        
        return [
            WeakPoint(
                topic=wp["topic"],
                mastery=wp["mastery"],
                questions_count=wp["questions_count"],
                priority=wp["priority"],
                recommendation=wp["recommendation"]
            )
            for wp in weak_points_data
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取薄弱点失败: {str(e)}")

@router.get("/recommendations")
async def get_study_recommendations(
    request: Request,
    user_id: str = Depends(get_user_id)
):
    """获取个性化学习建议"""
    try:
        study_plan = await analytics_service.generate_study_plan(user_id)
        weak_points = await analytics_service.identify_weak_points(user_id)
        
        if not study_plan:
            raise HTTPException(status_code=404, detail="无法生成学习建议")
        
        # 基于薄弱点推荐下一步学习主题
        next_topics = [wp["topic"] for wp in weak_points[:3]]
        
        # 基于当前水平推荐难度
        current_level = study_plan.get("current_level", "中等")
        suggested_difficulty = {
            "需要加强": "基础",
            "中等": "中级", 
            "良好": "中级",
            "优秀": "高级"
        }.get(current_level, "中级")
        
        daily_goals = study_plan.get("daily_goals", {})
        
        return {
            "next_topics": next_topics,
            "suggested_difficulty": suggested_difficulty,
            "estimated_study_time": daily_goals.get("study_time_minutes", 45),
            "focus_areas": daily_goals.get("focus_topics", []),
            "current_level": current_level,
            "daily_questions_target": daily_goals.get("questions_count", 10),
            "recommendations": study_plan.get("recommendations", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学习建议失败: {str(e)}")

@router.post("/analyze")
async def trigger_analysis(
    request: Request,
    user_id: str = Depends(get_user_id)
):
    """触发学习数据分析"""
    try:
        # 创建分析任务
        task_id = await task_manager.submit_task(
            "user_analysis",
            analytics_service.analyze_user_performance,
            user_id=user_id
        )
        
        return {
            "message": "分析任务已启动",
            "task_id": task_id,
            "estimated_time": "1-2分钟",
            "status_endpoint": f"/api/tasks/{task_id}/status"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动分析任务失败: {str(e)}")

@router.get("/summary")
async def get_learning_summary(
    request: Request,
    user_id: str = Depends(get_user_id)
):
    """获取学习总结"""
    try:
        performance = await analytics_service.analyze_user_performance(user_id)
        progress = await analytics_service.track_learning_progress(user_id, 7)
        
        achievements = progress.get("achievements", [])
        trends = progress.get("trends", {})
        
        return {
            "user_id": user_id,
            "summary_date": datetime.now().isoformat(),
            "overall_progress": {
                "accuracy_rate": performance.get("accuracy_rate", 0),
                "total_questions": performance.get("total_questions", 0),
                "study_sessions": performance.get("study_sessions", 0),
                "total_study_hours": performance.get("total_study_time", 0) / 60
            },
            "recent_trends": trends,
            "achievements": achievements,
            "consistency_score": progress.get("trends", {}).get("consistency", 0),
            "next_milestone": "连续练习30天" if len(achievements) < 5 else "准确率达到90%"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学习总结失败: {str(e)}") 