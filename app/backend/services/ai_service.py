"""
AI服务模块 - 处理AI相关任务
"""

import asyncio
from typing import List, Dict, Optional
from core.config import settings

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
    
    async def generate_podcast_script(self, topics: List[str], duration_minutes: int = 15) -> Dict:
        """生成播客脚本"""
        if not self.openai_client:
            return {"error": "AI服务不可用"}
        
        try:
            topics_str = "、".join(topics)
            prompt = f"""
            创建一个{duration_minutes}分钟的软件架构师学习播客脚本，主题包括：{topics_str}
            
            要求：
            1. 对话形式，有主持人和嘉宾两个角色
            2. 内容要通俗易懂，适合考试复习
            3. 包含实际案例和应用场景
            4. 时长约{duration_minutes}分钟（约{duration_minutes * 150}字）
            
            请按以下JSON格式输出：
            {{
                "title": "播客标题",
                "description": "播客描述",
                "segments": [
                    {{
                        "speaker": "主持人|嘉宾",
                        "content": "对话内容",
                        "timestamp": "00:00"
                    }}
                ]
            }}
            """
            
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
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
                model=settings.OPENAI_MODEL,
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

# 全局AI服务实例
ai_service = AIService()

# 导出的异步函数供调度器使用
async def generate_daily_podcast():
    """生成每日播客任务"""
    print("🎙️ 开始生成每日播客...")
    # TODO: 根据用户学习情况生成个性化播客
    pass

async def analyze_user_progress():
    """分析用户学习进度任务"""
    print("📊 开始分析用户学习进度...")
    # TODO: 定期分析所有用户的学习数据
    pass 