"""
LLM Service - 统一 LLM 客户端单例

提供统一的 LLM 调用接口，避免多处重复创建 AsyncOpenAI 实例。
"""
import json
import logging
from typing import Any, Optional

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    LLM 服务单例
    
    统一管理 LLM 客户端实例，提供 chat 和 chat_with_json 方法。
    """
    _instance: Optional["LLMService"] = None
    _client: Optional[AsyncOpenAI] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_API_BASE_URL,
            )
            self._model = settings.LLM_MODEL_NAME
            logger.info(f"LLMService initialized with model: {self._model}")

    @property
    def client(self) -> AsyncOpenAI:
        return self._client

    @property
    def model(self) -> str:
        return self._model

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
    ) -> dict:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            tools: 工具定义列表
            tool_choice: 工具选择
            
        Returns:
            LLM 响应
        """
        params = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
        }

        if tools:
            params["tools"] = tools
            if tool_choice:
                params["tool_choice"] = tool_choice

        response = await self._client.chat.completions.create(**params)
        return response.choices[0].message.model_dump()

    async def chat_with_json(
        self,
        messages: list[dict],
        temperature: float = 0.7,
    ) -> dict:
        """
        发送聊天请求，要求返回 JSON
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            
        Returns:
            解析后的 JSON 响应
        """
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return json.loads(content)

    async def chat_raw(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        **kwargs,
    ) -> dict:
        """
        发送原始聊天请求，直接返回响应对象
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            **kwargs: 其他 OpenAI 参数
            
        Returns:
            原始响应对象
        """
        params = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            **kwargs,
        }
        return await self._client.chat.completions.create(**params)


# 全局单例
llm_service = LLMService()
