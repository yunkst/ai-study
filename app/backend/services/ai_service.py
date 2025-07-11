"""
AI服务模块 - 处理AI相关任务
"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from core.config import settings
from services.analytics_service import analytics_service

class AIService:
    """AI服务主类"""
    
    def __init__(self):
        self.openai_client = None
        self._init_clients()
    
    def _init_clients(self):
        """初始化AI客户端"""
        if settings.OPENAI_API_KEY:
            import openai
            self.openai_client = openai.AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY
            )
            print("✅ OpenAI客户端初始化完成")
        else:
            print("⚠️ 未设置OPENAI_API_KEY，AI功能将不可用")
    
    async def generate_question_explanation(self, question: str, answer: str) -> str:
        """生成题目解析"""
        if not self.openai_client:
            return "AI服务不可用，无法生成解析"
        
        try:
            prompt = f"""
            作为软件架构师考试辅导专家，请为以下题目提供详细解析：
            
            题目：{question}
            正确答案：{answer}
            
            请从以下角度分析：
            1. 题目考查的知识点
            2. 解题思路和方法
            3. 相关的架构概念和原理
            4. 常见错误和注意事项
            """
            
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI解析生成失败: {e}")
            return "解析生成失败，请稍后重试"
    
    async def generate_podcast_script(self, topics: List[str], duration_minutes: int = 15, style: str = "conversation") -> Dict:
        """生成播客脚本"""
        if not self.openai_client:
            return {"error": "AI服务不可用"}
        
        try:
            topics_str = "、".join(topics)
            
            # 根据风格调整prompt
            style_prompts = {
                "conversation": "对话形式，有主持人和嘉宾两个角色进行互动讨论",
                "lecture": "讲座形式，由专家进行系统性讲解",
                "qa": "问答形式，通过问题和回答来展开内容"
            }
            
            style_prompt = style_prompts.get(style, style_prompts["conversation"])
            
            prompt = f"""
            创建一个{duration_minutes}分钟的软件架构师学习播客脚本，主题包括：{topics_str}
            
            要求：
            1. {style_prompt}
            2. 内容要通俗易懂，适合考试复习
            3. 包含实际案例和应用场景
            4. 时长约{duration_minutes}分钟（约{duration_minutes * 150}字）
            5. 重点突出实用性和考试要点
            
            请按以下JSON格式输出：
            {{
                "title": "播客标题",
                "description": "播客描述",
                "segments": [
                    {{
                        "speaker": "主持人|嘉宾|专家",
                        "content": "对话内容",
                        "timestamp": "00:00"
                    }}
                ]
            }}
            """
            
            response = await self.openai_client.chat.completions.create(
                model=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.8
            )
            
            import json
            try:
                script = json.loads(response.choices[0].message.content)
                return script
            except:
                return {
                    "title": f"软件架构学习：{topics_str}",
                    "description": "AI生成的学习播客",
                    "content": response.choices[0].message.content
                }
                
        except Exception as e:
            print(f"播客脚本生成失败: {e}")
            return {"error": f"脚本生成失败: {str(e)}"}
    
    async def analyze_learning_progress(self, user_data: Dict) -> Dict:
        """分析学习进度"""
        if not self.openai_client:
            return {"error": "AI服务不可用"}
        
        try:
            prompt = f"""
            分析以下学习数据，提供个性化建议：
            
            学习数据：{user_data}
            
            请分析：
            1. 当前学习状态评估
            2. 薄弱知识点识别
            3. 学习建议和计划
            4. 预计通过考试的时间
            
            用JSON格式返回分析结果。
            """
            
            response = await self.openai_client.chat.completions.create(
                model=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.6
            )
            
            import json
            try:
                analysis = json.loads(response.choices[0].message.content)
                return analysis
            except:
                return {"analysis": response.choices[0].message.content}
                
        except Exception as e:
            print(f"学习分析失败: {e}")
            return {"error": f"分析失败: {str(e)}"}
    
    async def generate_personalized_podcast_topics(self, user_id: str = "default") -> List[str]:
        """根据用户学习情况生成个性化播客主题"""
        try:
            # 获取用户分析数据
            user_performance = await analytics_service.analyze_user_performance(user_id)
            weak_points = await analytics_service.identify_weak_points(user_id)
            
            # 提取薄弱知识点
            weak_topics = [wp["topic"] for wp in weak_points[:3]]
            
            if weak_topics:
                return weak_topics
            else:
                # 默认热门主题
                return ["软件架构设计", "设计模式应用", "系统性能优化"]
                
        except Exception as e:
            print(f"生成个性化主题失败: {e}")
            return ["软件架构基础", "架构设计原则", "架构模式"]
    
    async def generate_learning_recommendations(self, user_id: str = "default") -> Dict:
        """生成学习建议"""
        try:
            user_performance = await analytics_service.analyze_user_performance(user_id)
            weak_points = await analytics_service.identify_weak_points(user_id)
            
            if not self.openai_client:
                return self._generate_basic_recommendations(user_performance, weak_points)
            
            # 使用AI生成更智能的建议
            prompt = f"""
            基于以下学习数据，生成详细的学习建议：
            
            用户表现：
            - 总体准确率：{user_performance.get('accuracy_rate', 0):.2%}
            - 总练习题目：{user_performance.get('total_questions', 0)}
            - 学习会话：{user_performance.get('study_sessions', 0)}
            
            薄弱知识点：
            {[wp['topic'] for wp in weak_points]}
            
            请提供：
            1. 当前学习状态评估
            2. 具体的改进建议
            3. 推荐的学习计划
            4. 重点关注的知识点
            
            返回JSON格式的建议。
            """
            
            response = await self.openai_client.chat.completions.create(
                model=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.6
            )
            
            import json
            try:
                recommendations = json.loads(response.choices[0].message.content)
                return recommendations
            except:
                return {
                    "status": "AI分析完成",
                    "recommendations": response.choices[0].message.content,
                    "weak_points": weak_points
                }
                
        except Exception as e:
            print(f"生成学习建议失败: {e}")
            return self._generate_basic_recommendations(user_performance, weak_points)
    
    def _generate_basic_recommendations(self, user_performance: Dict, weak_points: List[Dict]) -> Dict:
        """生成基础学习建议"""
        accuracy = user_performance.get('accuracy_rate', 0)
        
        if accuracy >= 0.9:
            status = "学习状态优秀，建议挑战更高难度"
        elif accuracy >= 0.8:
            status = "学习状态良好，继续保持"
        elif accuracy >= 0.7:
            status = "学习状态一般，需要加强练习"
        else:
            status = "需要重点关注基础知识"
        
        recommendations = [
            "每日保持至少30分钟的学习时间",
            "重点练习薄弱知识点相关题目",
            "定期复习已掌握的内容"
        ]
        
        if weak_points:
            recommendations.insert(1, f"优先学习：{', '.join([wp['topic'] for wp in weak_points[:3]])}")
        
        return {
            "status": status,
            "recommendations": recommendations,
            "weak_points": weak_points,
            "next_review_date": (datetime.now() + timedelta(days=3)).isoformat()
        }

# 全局AI服务实例
ai_service = AIService()

# 导出的异步函数供调度器使用
async def generate_daily_podcast():
    """生成每日播客任务"""
    print("🎙️ 开始生成每日播客...")
    try:
        # 根据用户学习情况生成个性化播客主题
        topics = await ai_service.generate_personalized_podcast_topics()
        
        print(f"今日播客主题: {', '.join(topics)}")
        
        # 生成播客脚本
        script = await ai_service.generate_podcast_script(
            topics=topics,
            duration_minutes=15,
            style="conversation"
        )
        
        if "error" not in script:
            print(f"✅ 每日播客脚本生成完成: {script.get('title', '未知标题')}")
            
            # 这里可以触发TTS生成和播客创建流程
            # 例如：await create_podcast_from_script(script)
            
        else:
            print(f"❌ 播客生成失败: {script['error']}")
            
    except Exception as e:
        print(f"每日播客生成任务失败: {e}")

async def analyze_all_users_progress():
    """分析所有用户学习进度任务"""
    print("📊 开始分析所有用户学习进度...")
    try:
        # 这里可以获取所有用户列表
        # users = get_all_users()
        
        # 分析默认用户作为示例
        users = ["default"]
        
        for user_id in users:
            try:
                print(f"正在分析用户 {user_id} 的学习进度...")
                
                # 获取用户表现数据
                performance = await analytics_service.analyze_user_performance(user_id)
                
                # 生成AI建议
                recommendations = await ai_service.generate_learning_recommendations(user_id)
                
                print(f"用户 {user_id} 分析完成:")
                print(f"  - 准确率: {performance.get('accuracy_rate', 0):.2%}")
                print(f"  - 状态: {recommendations.get('status', '未知')}")
                
                # 保存分析结果
                await analytics_service.save_analysis_results(user_id, {
                    "performance": performance,
                    "recommendations": recommendations,
                    "analysis_date": datetime.now().isoformat()
                })
                
            except Exception as user_error:
                print(f"用户 {user_id} 分析失败: {user_error}")
        
        print("✅ 所有用户进度分析完成")
        
    except Exception as e:
        print(f"用户进度分析任务失败: {e}")

async def generate_study_insights():
    """生成学习洞察报告"""
    print("🧠 开始生成学习洞察报告...")
    try:
        # 获取整体学习数据
        overall_performance = await analytics_service.analyze_user_performance("default")
        
        # 生成洞察
        insights = await ai_service.analyze_learning_progress(overall_performance)
        
        print(f"✅ 学习洞察生成完成")
        print(f"主要发现: {insights.get('analysis', '无特殊发现')[:100]}...")
        
        return insights
        
    except Exception as e:
        print(f"学习洞察生成失败: {e}")
        return {} 