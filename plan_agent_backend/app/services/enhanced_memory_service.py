"""
增强的长期记忆服务

整合向量搜索的长期记忆系统。
"""
import json
import logging
from typing import Any

from app.dependencies import SessionLocal
from app.models import UserMemory
from app.models_memory import MemoryEmbedding
from app.services.embedding_service import embedding_service
from app.services.semantic_search_service import semantic_search_service

logger = logging.getLogger(__name__)


class EnhancedLongTermMemory:
    """
    增强的长期记忆服务
    
    整合关键词搜索和向量语义搜索。
    """
    
    def __init__(self):
        self.embedding_service = embedding_service
        self.semantic_service = semantic_search_service
    
    async def add_memory(
        self,
        user_id: int,
        memory_type: str,
        content: str | dict,
        context: dict | None = None,
        generate_embedding: bool = True,
    ) -> int:
        """
        添加记忆（同时创建向量索引）
        
        Args:
            user_id: 用户 ID
            memory_type: 记忆类型 (如 'preference', 'goal', 'reflection')
            content: 记忆内容 (字符串或 JSON dict)
            context: 额外上下文
            generate_embedding: 是否生成向量索引
            
        Returns:
            memory_id
        """
        # 将 content 转为 JSONB 兼容格式
        if isinstance(content, dict):
            content_json = content
            content_text = json.dumps(content, ensure_ascii=False)
        else:
            content_json = {"text": content}
            content_text = content
        
        with SessionLocal() as db:
            # 创建记忆
            memory = UserMemory(
                user_id=user_id,
                memory_type=memory_type,
                content=content_json,
                context=context,
            )
            db.add(memory)
            db.commit()
            db.refresh(memory)
            memory_id = memory.id
            
            # 生成向量索引
            if generate_embedding:
                await self._create_embedding(memory_id, user_id, memory_type, content_text)
            
            return memory_id
    
    async def _create_embedding(
        self,
        memory_id: int,
        user_id: int,
        memory_type: str,
        content: str,
    ) -> bool:
        """为记忆创建向量索引"""
        try:
            # 生成向量
            vector = await self.embedding_service.generate_embedding(content)
            vector_bytes = self.embedding_service.vector_to_bytes(vector)
            
            with SessionLocal() as db:
                embedding = MemoryEmbedding(
                    memory_id=memory_id,
                    user_id=user_id,
                    memory_type=memory_type,
                    embedding=vector_bytes,
                )
                db.add(embedding)
                db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to create embedding for memory {memory_id}: {e}")
            return False
    
    async def add_memory_batch(
        self,
        memories: list[dict],
        generate_embeddings: bool = True,
    ) -> list[int]:
        """
        批量添加记忆
        
        Args:
            memories: 记忆列表，每项包含 user_id, memory_type, content, context
            generate_embeddings: 是否批量生成向量索引
            
        Returns:
            memory_id 列表
        """
        memory_ids = []
        
        # 批量创建记忆
        with SessionLocal() as db:
            for mem in memories:
                if isinstance(mem["content"], dict):
                    content_json = mem["content"]
                    content_text = json.dumps(mem["content"], ensure_ascii=False)
                else:
                    content_json = {"text": mem["content"]}
                    content_text = mem["content"]
                
                memory = UserMemory(
                    user_id=mem["user_id"],
                    memory_type=mem["memory_type"],
                    content=content_json,
                    context=mem.get("context"),
                )
                db.add(memory)
                memory_ids.append(memory)
            
            db.commit()
            
            # 刷新获取 ID
            for mem_obj in memory_ids:
                db.refresh(mem_obj)
            
            memory_ids = [m.id for m in memory_ids]
        
        # 批量生成向量
        if generate_embeddings:
            await self._create_embeddings_batch(memory_ids, memories)
        
        return memory_ids
    
    async def _create_embeddings_batch(
        self,
        memory_ids: list[int],
        memories: list[dict],
    ) -> bool:
        """批量创建向量索引"""
        try:
            # 批量生成向量
            texts = []
            for mem in memories:
                if isinstance(mem["content"], dict):
                    texts.append(json.dumps(mem["content"], ensure_ascii=False))
                else:
                    texts.append(mem["content"])
            
            vectors = await self.embedding_service.generate_embeddings(texts)
            
            # 批量存储
            with SessionLocal() as db:
                for memory_id, vector, mem in zip(memory_ids, vectors, memories):
                    vector_bytes = self.embedding_service.vector_to_bytes(vector)
                    embedding = MemoryEmbedding(
                        memory_id=memory_id,
                        user_id=mem["user_id"],
                        memory_type=mem["memory_type"],
                        embedding=vector_bytes,
                    )
                    db.add(embedding)
                
                db.commit()
            
            return True
        except Exception as e:
            logger.error(f"Failed to create batch embeddings: {e}")
            return False
    
    def get_recent_memories(
        self,
        user_id: int,
        memory_type: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """获取最近的记忆（按时间排序）"""
        with SessionLocal() as db:
            query = db.query(UserMemory).filter(UserMemory.user_id == user_id)
            
            if memory_type:
                query = query.filter(UserMemory.memory_type == memory_type)
            
            memories = query.order_by(UserMemory.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": m.id,
                    "type": m.memory_type,
                    "content": m.content,
                    "context": m.context,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in memories
            ]
    
    async def search_memories(
        self,
        user_id: int,
        query: str,
        memory_type: str | None = None,
        use_semantic: bool = True,
        limit: int = 5,
    ) -> list[dict]:
        """
        搜索记忆（支持语义搜索）
        
        Args:
            user_id: 用户 ID
            query: 查询文本
            memory_type: 记忆类型过滤
            use_semantic: 是否使用语义搜索 (False 则使用关键词)
            limit: 返回数量
            
        Returns:
            匹配的記憶列表
        """
        if not use_semantic:
            # 关键词搜索
            return self._keyword_search(user_id, query, memory_type, limit)
        
        # 语义搜索
        return await self._semantic_search(user_id, query, memory_type, limit)
    
    async def _semantic_search(
        self,
        user_id: int,
        query: str,
        memory_type: str | None,
        limit: int,
    ) -> list[dict]:
        """语义向量搜索"""
        try:
            # 生成查询向量
            vector = await self.embedding_service.generate_embedding(query)
            vector_bytes = self.embedding_service.vector_to_bytes(vector)
            
            # 向量相似度搜索
            results = self.semantic_service.search_similar(
                query_embedding=vector_bytes,
                user_id=user_id,
                memory_type=memory_type,
                limit=limit,
                similarity_threshold=0.6,  # 可调整
            )
            
            return results
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            # 回退到关键词搜索
            return self._keyword_search(user_id, query, memory_type, limit)
    
    def _keyword_search(
        self,
        user_id: int,
        keyword: str,
        memory_type: str | None,
        limit: int,
    ) -> list[dict]:
        """关键词搜索"""
        with SessionLocal() as db:
            query = db.query(UserMemory).filter(
                UserMemory.user_id == user_id,
                UserMemory.content.cast(str).ilike(f"%{keyword}%")
            )
            
            if memory_type:
                query = query.filter(UserMemory.memory_type == memory_type)
            
            memories = query.order_by(UserMemory.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": m.id,
                    "type": m.memory_type,
                    "content": m.content,
                    "context": m.context,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "similarity": 1.0,  # 关键词搜索无相似度
                }
                for m in memories
            ]
    
    def get_user_profile(self, user_id: int) -> dict:
        """获取用户画像"""
        memories = self.get_recent_memories(user_id, limit=50)
        
        # 聚合偏好
        preferences = {}
        goals = []
        reflections = []
        
        for memory in memories:
            mem_type = memory["type"]
            content = memory["content"]
            
            if mem_type == "preference":
                if isinstance(content, dict):
                    preferences.update(content)
                else:
                    preferences[content] = True
            
            elif mem_type == "goal":
                goals.append(content)
            
            elif mem_type == "reflection":
                reflections.append(content)
        
        return {
            "preferences": preferences,
            "recent_goals": goals[:5],
            "recent_reflections": reflections[:5],
            "total_memories": len(memories),
        }
    
    def rebuild_embeddings(
        self,
        user_id: int | None = None,
        memory_type: str | None = None,
    ) -> dict:
        """
        重建向量索引
        
        用于修复缺失的向量或批量重新生成。
        """
        with SessionLocal() as db:
            # 查找没有向量的记忆
            query = db.query(UserMemory).outerjoin(
                MemoryEmbedding,
                UserMemory.id == MemoryEmbedding.memory_id
            ).filter(MemoryEmbedding.id == None)
            
            if user_id:
                query = query.filter(UserMemory.user_id == user_id)
            if memory_type:
                query = query.filter(UserMemory.memory_type == memory_type)
            
            memories = query.all()
        
        import asyncio
        # 同步调用批量生成（实际使用时建议用 celery 等异步处理）
        asyncio.create_task(
            self._rebuild_embeddings_async([m.id for m in memories], user_id, memory_type)
        )
        
        return {
            "total_missing": len(memories),
            "status": "rebuilding in background",
        }
    
    async def _rebuild_embeddings_async(
        self,
        memory_ids: list[int],
        user_id: int | None,
        memory_type: str | None,
    ):
        """异步重建向量"""
        # 获取记忆内容
        with SessionLocal() as db:
            memories = db.query(UserMemory).filter(
                UserMemory.id.in_(memory_ids)
            ).all()
        
        texts = []
        for m in memories:
            if isinstance(m.content, dict):
                texts.append(json.dumps(m.content, ensure_ascii=False))
            else:
                texts.append(str(m.content))
        
        # 批量生成
        vectors = await self.embedding_service.generate_embeddings(texts)
        
        # 批量存储
        with SessionLocal() as db:
            for memory, vector in zip(memories, vectors):
                vector_bytes = self.embedding_service.vector_to_bytes(vector)
                embedding = MemoryEmbedding(
                    memory_id=memory.id,
                    user_id=memory.user_id,
                    memory_type=memory.memory_type,
                    embedding=vector_bytes,
                )
                db.add(embedding)
            
            db.commit()
        
        logger.info(f"Rebuilt {len(memory_ids)} embeddings")


# 全局实例
enhanced_long_term_memory = EnhancedLongTermMemory()
