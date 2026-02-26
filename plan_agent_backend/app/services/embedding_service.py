"""
向量嵌入服务 - 多 API 自动切换

支持配置多个 Embedding API 提供商，当一个失败时自动切换到下一个。
"""
import json
import logging
from typing import Any

import numpy as np
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError

from app.config import settings
from app.utils.timezone import get_utc_now

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """单个 Embedding API 提供商"""
    
    def __init__(self, url: str, key: str, model: str, name: str = None):
        self.url = url
        self.key = key
        self.model = model
        self.name = name or url
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化客户端"""
        self.client = AsyncOpenAI(
            api_key=self.key,
            base_url=self.url,
        )
    
    def __repr__(self):
        return f"<Provider: {self.name}, model: {self.model}>"


class MultiProviderEmbeddingService:
    """
    多提供商向量嵌入服务
    
    支持配置多个 API 提供商，自动失败重试。
    """
    
    # 默认维度 (text-embedding-3-small)
    DIMENSION = 1536
    
    def __init__(self):
        self.providers: list[EmbeddingProvider] = []
        self._init_providers()
    
    def _init_providers(self):
        """初始化所有提供商"""
        # 1. 尝试从 EMBEDDING_PROVIDERS 加载
        providers_config = []
        if settings.EMBEDDING_PROVIDERS:
            try:
                providers_config = json.loads(settings.EMBEDDING_PROVIDERS)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse EMBEDDING_PROVIDERS: {e}")
        
        # 2. 如果没有配置，回退到旧的单 API 配置
        if not providers_config:
            if settings.EMBEDDING_API_KEY or settings.LLM_API_KEY:
                providers_config = [{
                    "url": settings.EMBEDDING_API_BASE_URL or settings.LLM_API_BASE_URL,
                    "key": settings.EMBEDDING_API_KEY or settings.LLM_API_KEY,
                    "model": settings.EMBEDDING_MODEL,
                }]
        
        # 3. 创建提供商实例
        for i, config in enumerate(providers_config):
            try:
                provider = EmbeddingProvider(
                    url=config.get("url", ""),
                    key=config.get("key", ""),
                    model=config.get("model", "text-embedding-3-small"),
                    name=config.get("name", f"provider_{i}"),
                )
                if provider.key:  # 只添加有 key 的提供商
                    self.providers.append(provider)
                    logger.info(f"Loaded embedding provider: {provider.name}")
            except Exception as e:
                logger.warning(f"Failed to load provider {i}: {e}")
        
        if not self.providers:
            logger.warning("No embedding providers configured!")
    
    @property
    def current_provider(self) -> EmbeddingProvider | None:
        """获取当前使用的提供商"""
        return self.providers[0] if self.providers else None
    
    def get_provider_info(self) -> list[dict]:
        """获取所有提供商信息"""
        return [
            {
                "name": p.name,
                "url": p.url,
                "model": p.model,
            }
            for p in self.providers
        ]
    
    async def _call_provider(
        self, 
        provider: EmbeddingProvider, 
        texts: list[str],
        single: bool = False,
    ) -> list[list[float]]:
        """调用单个提供商"""
        try:
            if single:
                response = await provider.client.embeddings.create(
                    model=provider.model,
                    input=texts[0],
                )
                return [response.data[0].embedding]
            else:
                response = await provider.client.embeddings.create(
                    model=provider.model,
                    input=texts,
                )
                return [item.embedding for item in response.data]
        except RateLimitError as e:
            logger.warning(f"Rate limit for {provider.name}: {e}")
            raise
        except APITimeoutError as e:
            logger.warning(f"Timeout for {provider.name}: {e}")
            raise
        except APIError as e:
            logger.warning(f"API error for {provider.name}: {e}")
            raise
        except Exception as e:
            logger.warning(f"Unknown error for {provider.name}: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> list[float]:
        """
        生成文本的向量嵌入
        
        自动尝试所有配置的 API 提供商。
        
        Args:
            text: 输入文本
            
        Returns:
            向量数组
        """
        if not text:
            return [0.0] * self.DIMENSION
        
        results = await self.generate_embeddings([text])
        return results[0] if results else [0.0] * self.DIMENSION
    
    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        批量生成向量嵌入
        
        自动失败重试：当前一个 API 失败时，自动切换到下一个。
        
        Args:
            texts: 输入文本列表
            
        Returns:
            向量数组列表
        """
        if not texts:
            return []
        
        if not self.providers:
            logger.error("No embedding providers available!")
            return [[0.0] * self.DIMENSION for _ in texts]
        
        last_error = None
        
        # 依次尝试每个提供商
        for i, provider in enumerate(self.providers):
            try:
                logger.debug(f"Trying provider {provider.name} ({i+1}/{len(self.providers)})")
                
                # 检查文本数量，决定是否分批
                if len(texts) == 1:
                    result = await self._call_provider(provider, texts, single=True)
                else:
                    # 批量调用
                    result = await self._call_provider(provider, texts)
                
                # 成功
                logger.info(f"Successfully generated embeddings using {provider.name}")
                return result
                
            except (RateLimitError, APITimeoutError, APIError) as e:
                last_error = e
                logger.warning(f"Provider {provider.name} failed: {e}, trying next...")
                continue
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider.name} failed: {e}, trying next...")
                continue
        
        # 所有提供商都失败
        logger.error(f"All {len(self.providers)} providers failed. Last error: {last_error}")
        return [[0.0] * self.DIMENSION for _ in texts]
    
    async def generate_embeddings_streaming(
        self,
        texts: list[str],
        batch_size: int = 100,
    ) -> list[list[float]]:
        """
        流式批量生成向量嵌入
        
        将大量文本分批处理，避免单次请求过大。
        
        Args:
            texts: 输入文本列表
            batch_size: 每批处理的数量 (默认 100)
            
        Returns:
            向量数组列表
        """
        if not texts:
            return []
        
        all_results = []
        
        # 分批处理
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.debug(f"Processing batch {i//batch_size + 1}, size: {len(batch)}")
            
            # 处理当前批次
            batch_results = await self.generate_embeddings(batch)
            all_results.extend(batch_results)
        
        return all_results
    
    async def generate_embeddings_async(
        self,
        texts: list[str],
        batch_size: int = 100,
        callback=None,
    ) -> list[list[float]]:
        """
        异步批量生成向量嵌入（带回调）
        
        适用于后台任务，每完成一批调用回调函数。
        
        Args:
            texts: 输入文本列表
            batch_size: 每批处理的数量
            callback: 每批完成后的回调函数 (batch_index, batch_results)
            
        Returns:
            向量数组列表
        """
        if not texts:
            return []
        
        all_results = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(texts))
            batch = texts[start_idx:end_idx]
            
            logger.info(f"Processing batch {batch_idx + 1}/{total_batches}")
            
            # 处理当前批次
            batch_results = await self.generate_embeddings(batch)
            all_results.extend(batch_results)
            
            # 调用回调
            if callback:
                try:
                    await callback(batch_idx, batch_results)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
        
        return all_results
    
    def vector_to_bytes(self, vector: list[float]) -> bytes:
        """将向量转换为字节存储（pgvector 格式）"""
        arr = np.array(vector, dtype=np.float32)
        return arr.tobytes()
    
    def bytes_to_vector(self, bytes_data: bytes) -> list[float]:
        """从字节转换为向量"""
        arr = np.frombuffer(bytes_data, dtype=np.float32)
        return arr.tolist()
    
    def cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """计算余弦相似度"""
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def get_config(self) -> dict:
        """获取当前配置信息"""
        return {
            "providers": self.get_provider_info(),
            "provider_count": len(self.providers),
            "current_provider": self.current_provider.name if self.current_provider else None,
            "dimension": self.DIMENSION,
        }


# 全局实例
embedding_service = MultiProviderEmbeddingService()
