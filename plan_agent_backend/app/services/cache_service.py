"""
Redis 缓存服务

提供分布式缓存能力，用于用户会话、热点数据等。
"""

import json
import logging
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Redis 客户端 (延迟初始化)
_redis_client = None


def get_redis_client():
    """获取 Redis 客户端 (单例)"""
    global _redis_client

    if not settings.REDIS_ENABLED:
        return None

    if _redis_client is None:
        try:
            import redis.asyncio as redis

            _redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info(f"Redis client initialized: {settings.REDIS_URL}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            return None

    return _redis_client


class CacheService:
    """
    缓存服务

    提供简洁的缓存操作接口，支持:
    - 用户会话缓存
    - 热点数据缓存
    - 通用键值缓存
    """

    # 缓存键前缀
    PREFIX_USER = "user:"  # 用户数据
    PREFIX_SESSION = "session:"  # 会话数据
    PREFIX_GOAL = "goal:"  # 目标数据
    PREFIX_TASK = "task:"  # 任务数据
    PREFIX_AGENT = "agent:"  # Agent 会话

    def __init__(self):
        self._client = None
        self._enabled = settings.REDIS_ENABLED

    @property
    def client(self):
        """获取 Redis 客户端"""
        if not self._enabled:
            return None
        if self._client is None:
            self._client = get_redis_client()
        return self._client

    def _serialize(self, value: Any) -> str:
        """序列化值"""
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        return json.dumps(value, ensure_ascii=False)

    def _deserialize(self, value: Optional[str]) -> Any:
        """反序列化值"""
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self.client:
            return None

        try:
            value = await self.client.get(key)
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Cache get error: {key} - {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """设置缓存值"""
        if not self.client:
            return False

        try:
            serialized = self._serialize(value)
            expire = ttl or settings.CACHE_TTL_DEFAULT
            await self.client.setex(key, expire, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {key} - {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.client:
            return False

        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {key} - {e}")
            return False

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.client:
            return False

        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error: {key} - {e}")
            return False

    async def get_user(self, user_id: int) -> Optional[dict]:
        """获取用户缓存"""
        key = f"{self.PREFIX_USER}{user_id}"
        return await self.get(key)

    async def set_user(self, user_id: int, user_data: dict, ttl: int = 300) -> bool:
        """设置用户缓存"""
        key = f"{self.PREFIX_USER}{user_id}"
        return await self.set(key, user_data, ttl)

    async def delete_user(self, user_id: int) -> bool:
        """删除用户缓存"""
        key = f"{self.PREFIX_USER}{user_id}"
        return await self.delete(key)

    async def get_agent_session(self, session_id: str) -> Optional[dict]:
        """获取 Agent 会话"""
        key = f"{self.PREFIX_AGENT}{session_id}"
        return await self.get(key)

    async def set_agent_session(
        self,
        session_id: str,
        session_data: dict,
        ttl: int = None,
    ) -> bool:
        """设置 Agent 会话"""
        key = f"{self.PREFIX_AGENT}{session_id}"
        return await self.set(key, session_data, ttl or settings.SESSION_CACHE_TTL)

    async def delete_agent_session(self, session_id: str) -> bool:
        """删除 Agent 会话"""
        key = f"{self.PREFIX_AGENT}{session_id}"
        return await self.delete(key)

    async def get_goals(self, user_id: int) -> Optional[list]:
        """获取用户目标列表缓存"""
        key = f"{self.PREFIX_GOAL}list:{user_id}"
        return await self.get(key)

    async def set_goals(self, user_id: int, goals: list, ttl: int = 60) -> bool:
        """设置用户目标列表缓存"""
        key = f"{self.PREFIX_GOAL}list:{user_id}"
        return await self.set(key, goals, ttl)

    async def invalidate_user_cache(self, user_id: int) -> list:
        """清除用户相关所有缓存"""
        if not self.client:
            return []

        patterns = [
            f"{self.PREFIX_USER}{user_id}",
            f"{self.PREFIX_GOAL}*{user_id}",
            f"{self.PREFIX_TASK}*{user_id}",
        ]

        deleted = []
        for pattern in patterns:
            try:
                keys = await self.client.keys(pattern)
                if keys:
                    await self.client.delete(*keys)
                    deleted.extend(keys)
            except Exception as e:
                logger.error(f"Cache invalidate error: {pattern} - {e}")

        return deleted


# 全局缓存服务实例
cache_service = CacheService()
