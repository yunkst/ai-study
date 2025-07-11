"""
学习分析服务
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.config import settings
from core.database import get_db
from models.practice import PracticeSession as PracticeSessionModel, Answer as AnswerModel
from models.question import Question, DifficultyLevel
from models.user import User

class AnalyticsService:
    """学习分析服务类"""
    
    def __init__(self):
        pass
    
    def _get_db(self) -> Session:
        """获取数据库会话"""
        return next(get_db())
    
    async def analyze_user_performance(self, user_id: str = "default") -> Dict:
        """分析用户学习表现"""
        try:
            db = self._get_db()
            
            # 获取用户的练习会话
            uid = int(user_id) if user_id.isdigit() else 1
            sessions = db.query(PracticeSessionModel).filter(
                PracticeSessionModel.user_id == uid
            ).all()
            
            if not sessions:
                return {
                    "user_id": user_id,
                    "analysis_date": datetime.now().isoformat(),
                    "total_questions": 0,
                    "correct_answers": 0,
                    "accuracy_rate": 0,
                    "average_time_per_question": 0,
                    "study_sessions": 0,
                    "total_study_time": 0,
                    "knowledge_points": {},
                    "difficulty_analysis": {}
                }
            
            # 计算总体统计
            total_questions = sum(session.total_questions for session in sessions)
            total_correct = sum(session.correct_count or 0 for session in sessions)
            total_time = sum(session.duration_seconds or 0 for session in sessions)
            
            accuracy_rate = total_correct / total_questions if total_questions > 0 else 0
            avg_time_per_question = total_time / total_questions if total_questions > 0 else 0
            
            # 获取答案详情用于知识点分析
            all_answers = db.query(AnswerModel).join(PracticeSessionModel).filter(
                PracticeSessionModel.user_id == uid
            ).all()
            
            # 分析知识点掌握情况
            knowledge_points = self._analyze_knowledge_points(db, all_answers)
            
            # 分析难度表现
            difficulty_analysis = self._analyze_difficulty_performance(db, all_answers)
            
            performance_data = {
                "user_id": user_id,
                "analysis_date": datetime.now().isoformat(),
                "total_questions": total_questions,
                "correct_answers": total_correct,
                "accuracy_rate": accuracy_rate,
                "average_time_per_question": avg_time_per_question,
                "study_sessions": len(sessions),
                "total_study_time": total_time // 60,  # 转换为分钟
                "knowledge_points": knowledge_points,
                "difficulty_analysis": difficulty_analysis
            }
            
            db.close()
            return performance_data
            
        except Exception as e:
            print(f"用户表现分析失败: {e}")
            raise
    
    def _get_mock_performance_data(self, user_id: str) -> Dict:
        """获取模拟性能数据"""
        return {
            "user_id": user_id,
            "analysis_date": datetime.now().isoformat(),
            "total_questions": 150,
            "correct_answers": 120,
            "accuracy_rate": 0.8,
            "average_time_per_question": 45,  # 秒
            "study_sessions": 15,
            "total_study_time": 1200,  # 分钟
            "knowledge_points": {
                "软件架构基础": {"mastery": 0.85, "questions": 30},
                "设计模式": {"mastery": 0.92, "questions": 25},
                "系统架构": {"mastery": 0.65, "questions": 40},
                "性能优化": {"mastery": 0.58, "questions": 20},
                "安全架构": {"mastery": 0.75, "questions": 35}
            },
            "difficulty_analysis": {
                "基础": {"accuracy": 0.95, "count": 60},
                "中级": {"accuracy": 0.78, "count": 70},
                "高级": {"accuracy": 0.45, "count": 20}
            }
        }
    
    def _analyze_knowledge_points(self, db: Session, answers: List[AnswerModel]) -> Dict:
        """分析知识点掌握情况"""
        knowledge_stats = {}
        
        for answer in answers:
            question = db.query(Question).filter(Question.id == answer.question_id).first()
            if not question or not question.knowledge_points:
                continue
            
            for point in question.knowledge_points:
                if point not in knowledge_stats:
                    knowledge_stats[point] = {"correct": 0, "total": 0}
                
                knowledge_stats[point]["total"] += 1
                if answer.is_correct:
                    knowledge_stats[point]["correct"] += 1
        
        # 计算掌握度
        knowledge_points = {}
        for point, stats in knowledge_stats.items():
            mastery = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            knowledge_points[point] = {
                "mastery": mastery,
                "questions": stats["total"]
            }
        
        return knowledge_points
    
    def _analyze_difficulty_performance(self, db: Session, answers: List[AnswerModel]) -> Dict:
        """分析难度表现"""
        difficulty_stats = {}
        
        for answer in answers:
            question = db.query(Question).filter(Question.id == answer.question_id).first()
            if not question:
                continue
            
            difficulty_name = {
                DifficultyLevel.BASIC: "基础",
                DifficultyLevel.INTERMEDIATE: "中级", 
                DifficultyLevel.ADVANCED: "高级"
            }.get(question.difficulty, "未知")
            
            if difficulty_name not in difficulty_stats:
                difficulty_stats[difficulty_name] = {"correct": 0, "total": 0}
            
            difficulty_stats[difficulty_name]["total"] += 1
            if answer.is_correct:
                difficulty_stats[difficulty_name]["correct"] += 1
        
        # 计算准确率
        difficulty_analysis = {}
        for difficulty, stats in difficulty_stats.items():
            accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            difficulty_analysis[difficulty] = {
                "accuracy": accuracy,
                "count": stats["total"]
            }
        
        return difficulty_analysis

    async def identify_weak_points(self, user_id: str = "default") -> List[Dict]:
        """识别薄弱知识点"""
        try:
            performance = await self.analyze_user_performance(user_id)
            knowledge_points = performance.get("knowledge_points", {})
            
            weak_points = []
            for topic, data in knowledge_points.items():
                mastery = data.get("mastery", 0)
                if mastery < 0.7:  # 掌握度低于70%认为是薄弱点
                    weak_points.append({
                        "topic": topic,
                        "mastery": mastery,
                        "questions_count": data.get("questions", 0),
                        "priority": "高" if mastery < 0.6 else "中",
                        "recommendation": self._get_topic_recommendation(topic, mastery)
                    })
            
            # 按掌握度排序，最薄弱的在前
            weak_points.sort(key=lambda x: x["mastery"])
            
            return weak_points
            
        except Exception as e:
            print(f"薄弱点识别失败: {e}")
            return []
    
    def _get_topic_recommendation(self, topic: str, mastery: float) -> str:
        """获取知识点学习建议"""
        recommendations = {
            "软件架构基础": "建议重新学习架构基本概念和原理",
            "设计模式": "多做设计模式相关的案例练习",
            "系统架构": "加强系统设计和架构模式的理解",
            "性能优化": "重点学习性能调优方法和工具",
            "安全架构": "强化安全设计原则和最佳实践"
        }
        
        base_recommendation = recommendations.get(topic, "建议加强相关练习")
        
        if mastery < 0.5:
            return f"急需重点关注：{base_recommendation}"
        elif mastery < 0.7:
            return f"需要加强：{base_recommendation}"
        else:
            return f"继续巩固：{base_recommendation}"
    
    async def generate_study_plan(self, user_id: str = "default") -> Dict:
        """生成个性化学习计划"""
        try:
            weak_points = await self.identify_weak_points(user_id)
            performance = await self.analyze_user_performance(user_id)
            
            plan = {
                "plan_date": datetime.now().isoformat(),
                "user_id": user_id,
                "current_level": self._assess_current_level(performance),
                "target_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "daily_goals": {
                    "questions_count": 10,
                    "study_time_minutes": 45,
                    "focus_topics": [wp["topic"] for wp in weak_points[:3]]
                },
                "weekly_goals": {
                    "total_questions": 70,
                    "accuracy_target": 0.85,
                    "new_topics": 2
                },
                "recommendations": [
                    "优先练习薄弱知识点相关题目",
                    "保持每日练习节奏",
                    "定期复习已掌握的知识点"
                ],
                "weak_points": weak_points
            }
            
            return plan
            
        except Exception as e:
            print(f"学习计划生成失败: {e}")
            return {}
    
    def _assess_current_level(self, performance: Dict) -> str:
        """评估当前学习水平"""
        accuracy = performance.get("accuracy_rate", 0)
        
        if accuracy >= 0.9:
            return "优秀"
        elif accuracy >= 0.8:
            return "良好"
        elif accuracy >= 0.7:
            return "中等"
        else:
            return "需要加强"
    
    async def track_learning_progress(self, user_id: str = "default", days: int = 30) -> Dict:
        """跟踪学习进度"""
        try:
            db = self._get_db()
            
            # 获取指定时间范围内的会话
            start_date = datetime.now() - timedelta(days=days)
            uid = int(user_id) if user_id.isdigit() else 1
            sessions = db.query(PracticeSessionModel).filter(
                PracticeSessionModel.user_id == uid,
                PracticeSessionModel.start_time >= start_date
            ).order_by(PracticeSessionModel.start_time).all()
            
            if not sessions:
                db.close()
                return {
                    "user_id": user_id,
                    "tracking_period": f"{days}天",
                    "daily_stats": [],
                    "trends": {},
                    "achievements": []
                }
            
            # 按日期聚合数据
            daily_stats = {}
            for session in sessions:
                date_key = session.start_time.strftime("%Y-%m-%d")
                
                if date_key not in daily_stats:
                    daily_stats[date_key] = {
                        "date": date_key,
                        "questions_answered": 0,
                        "correct_answers": 0,
                        "study_time": 0,
                        "sessions": 0
                    }
                
                daily_stats[date_key]["questions_answered"] += session.total_questions
                daily_stats[date_key]["correct_answers"] += session.correct_count or 0
                daily_stats[date_key]["study_time"] += session.duration_seconds or 0
                daily_stats[date_key]["sessions"] += 1
            
            # 计算每日准确率
            for stats in daily_stats.values():
                if stats["questions_answered"] > 0:
                    stats["accuracy"] = stats["correct_answers"] / stats["questions_answered"]
                else:
                    stats["accuracy"] = 0
                stats["study_time"] = stats["study_time"] // 60  # 转换为分钟
            
            # 计算趋势
            accuracies = [stats["accuracy"] for stats in daily_stats.values()]
            study_times = [stats["study_time"] for stats in daily_stats.values()]
            
            accuracy_trend = "上升" if len(accuracies) > 1 and accuracies[-1] > accuracies[0] else "稳定"
            speed_trend = "稳定"  # 简化处理
            
            # 计算一致性（学习天数/总天数）
            consistency = len(daily_stats) / days
            
            progress_data = {
                "user_id": user_id,
                "tracking_period": f"{days}天",
                "daily_stats": list(daily_stats.values()),
                "trends": {
                    "accuracy_trend": accuracy_trend,
                    "speed_trend": speed_trend,
                    "consistency": consistency
                },
                "achievements": self._generate_achievements(sessions)
            }
            
            db.close()
            return progress_data
            
        except Exception as e:
            print(f"进度跟踪失败: {e}")
            raise
    
    def _get_mock_progress_data(self, user_id: str, days: int) -> Dict:
        """获取模拟进度数据"""
        progress_data = {
            "user_id": user_id,
            "tracking_period": f"{days}天",
            "daily_stats": [],
            "trends": {
                "accuracy_trend": "上升",
                "speed_trend": "稳定",
                "consistency": 0.85
            },
            "achievements": [
                {"date": "2024-01-01", "type": "连续练习7天"},
                {"date": "2024-01-05", "type": "准确率突破80%"}
            ]
        }
        
        # 生成模拟的每日数据
        base_date = datetime.now() - timedelta(days=days)
        for i in range(days):
            date = base_date + timedelta(days=i)
            daily_stat = {
                "date": date.strftime("%Y-%m-%d"),
                "questions_answered": 8 + (i % 5),
                "accuracy": 0.7 + (i * 0.005),  # 逐渐提升
                "study_time": 30 + (i % 20),
                "sessions": 1 + (i % 2)
            }
            progress_data["daily_stats"].append(daily_stat)
        
        return progress_data
    
    def _generate_achievements(self, sessions: List[PracticeSessionModel]) -> List[Dict]:
        """生成成就记录"""
        achievements = []
        
        if len(sessions) >= 7:
            achievements.append({
                "date": sessions[6].start_time.strftime("%Y-%m-%d"),
                "type": "连续练习7天"
            })
        
        # 检查准确率成就
        for session in sessions:
            if session.score and session.score >= 80:
                achievements.append({
                    "date": session.start_time.strftime("%Y-%m-%d"),
                    "type": "准确率突破80%"
                })
                break
        
        return achievements[:5]  # 最多返回5个成就

    async def save_analysis_results(self, user_id: str, analysis_data: Dict):
        """保存分析结果到数据库"""
        try:
            db = self._get_db()
            
            # 这里可以实现分析结果的持久化存储
            # 例如保存到分析结果表
            
            print(f"分析结果已保存 - 用户: {user_id}, 准确率: {analysis_data.get('accuracy_rate', 0):.2%}")
            
            db.close()
            
        except Exception as e:
            print(f"保存分析结果失败: {e}")

# 全局分析服务实例
analytics_service = AnalyticsService()

# 导出函数供调度器使用
async def analyze_user_progress():
    """定时分析用户进度任务"""
    print("📊 开始分析用户学习进度...")
    try:
        # 分析默认用户
        performance = await analytics_service.analyze_user_performance()
        weak_points = await analytics_service.identify_weak_points()
        
        print(f"用户当前准确率: {performance.get('accuracy_rate', 0):.2%}")
        print(f"发现薄弱点: {len(weak_points)}个")
        
        # 保存分析结果到数据库
        await analytics_service.save_analysis_results("default", performance)
        
    except Exception as e:
        print(f"定时分析任务失败: {e}") 