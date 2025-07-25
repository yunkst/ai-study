"""AI服务模块

提供与AI模型交互的功能，包括生成题目等。
"""
import json
from collections.abc import AsyncGenerator

import httpx
from fastapi import HTTPException

from app.core.config import settings


class AIService:
    """AI服务类，用于与Dify API交互"""

    def __init__(self):
        self.base_url = settings.DIFY_API_URL
        self.api_key = settings.DIFY_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def stream_chat(
        self,
        message: str,
        user_id: str,
        conversation_id: str | None = None,
        context: str | None = None
    ) -> AsyncGenerator[str, None]:
        """流式聊天接口"""
        payload = {
            "inputs": {},
            "query": message,
            "response_mode": "streaming",
            "conversation_id": conversation_id or "",
            "user": str(user_id)
        }

        if context:
            payload["inputs"]["context"] = context

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/v1/chat-messages",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status_code != 200:
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"AI service error: {response.text}"
                        )

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            if data_str.strip() == "[DONE]":
                                break

                            try:
                                data = json.loads(data_str)
                                if data.get("event") == "message":
                                    content = data.get("answer", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to AI service: {str(e)}"
            ) from e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail="AI service error"
            ) from e

    async def get_explanation(
        self,
        question: str,
        user_answer: str,
        correct_answer: str,
        user_id: str
    ) -> str:
        """获取题目解析"""
        prompt = f"""
        请为以下题目提供详细解析：

        题目：{question}
        用户答案：{user_answer}
        正确答案：{correct_answer}

        请分析用户答案的对错，并提供详细的解题思路和知识点解释。
        """

        chunks = []
        async for chunk in self.stream_chat(prompt, user_id):
            chunks.append(chunk)
        full_response = "".join(chunks)

        return full_response

    async def get_hint(
        self,
        question: str,
        user_id: str
    ) -> str:
        """获取题目提示"""
        prompt = f"""
        请为以下题目提供解题提示，不要直接给出答案：

        题目：{question}

        请提供解题思路和相关知识点的提示。
        """

        chunks = []
        async for chunk in self.stream_chat(prompt, user_id):
            chunks.append(chunk)
        full_response = "".join(chunks)

        return full_response

ai_service = AIService()
