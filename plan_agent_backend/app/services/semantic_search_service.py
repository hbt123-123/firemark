"""
语义搜索服务

基于 pgvector 的向量相似度搜索。
"""
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies import SessionLocal
from app.models_memory import MemoryEmbedding

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """
    语义搜索服务
    
    使用 pgvector 进行向量相似度搜索。
    """
    
    def __init__(self):
        self._check_pgvector()
    
    def _check_pgvector(self) -> bool:
        """检查 pgvector 扩展是否可用"""
        try:
            with SessionLocal() as db:
                result = db.execute(text(
                    "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
                ))
                return result.scalar() is not None
        except Exception as e:
            logger.warning(f"pgvector not available: {e}")
            return False
    
    def enable_pgvector(self) -> bool:
        """在数据库中启用 pgvector 扩展"""
        try:
            with SessionLocal() as db:
                db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                db.commit()
                logger.info("pgvector extension enabled")
                return True
        except Exception as e:
            logger.error(f"Failed to enable pgvector: {e}")
            return False
    
    def search_similar(
        self,
        query_embedding: bytes,
        user_id: int,
        memory_type: str | None = None,
        limit: int = 5,
        similarity_threshold: float = 0.7,
    ) -> list[dict]:
        """
        搜索相似记忆
        
        Args:
            query_embedding: 查询向量 (bytes)
            user_id: 用户 ID
            memory_type: 记忆类型过滤 (可选)
            limit: 返回数量限制
            similarity_threshold: 相似度阈值
            
        Returns:
            相似记忆列表
        """
        try:
            with SessionLocal() as db:
                # 构建查询
                if memory_type:
                    sql = text("""
                        SELECT 
                            me.id,
                            me.memory_id,
                            me.user_id,
                            me.memory_type,
                            me.created_at,
                            um.content,
                            um.context,
                            1 - (me.embedding <=> :embedding::vector) as similarity
                        FROM memory_embeddings me
                        JOIN user_memories um ON me.memory_id = um.id
                        WHERE me.user_id = :user_id
                            AND me.memory_type = :memory_type
                            AND (me.embedding <=> :embedding::vector) < :threshold
                        ORDER BY me.embedding <=> :embedding::vector
                        LIMIT :limit
                    """)
                    result = db.execute(sql, {
                        "embedding": query_embedding,
                        "user_id": user_id,
                        "memory_type": memory_type,
                        "threshold": 1 - similarity_threshold,
                        "limit": limit,
                    })
                else:
                    sql = text("""
                        SELECT 
                            me.id,
                            me.memory_id,
                            me.user_id,
                            me.memory_type,
                            me.created_at,
                            um.content,
                            um.context,
                            1 - (me.embedding <=> :embedding::vector) as similarity
                        FROM memory_embeddings me
                        JOIN user_memories um ON me.memory_id = um.id
                        WHERE me.user_id = :user_id
                            AND (me.embedding <=> :embedding::vector) < :threshold
                        ORDER BY me.embedding <=> :embedding::vector
                        LIMIT :limit
                    """)
                    result = db.execute(sql, {
                        "embedding": query_embedding,
                        "user_id": user_id,
                        "threshold": 1 - similarity_threshold,
                        "limit": limit,
                    })
                
                rows = result.fetchall()
                return [
                    {
                        "id": row[0],
                        "memory_id": row[1],
                        "user_id": row[2],
                        "memory_type": row[3],
                        "created_at": row[4].isoformat() if row[4] else None,
                        "content": row[5],
                        "context": row[6],
                        "similarity": float(row[7]) if row[7] else 0.0,
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def search_by_keyword_and_similarity(
        self,
        query_embedding: bytes,
        user_id: int,
        keyword: str,
        memory_type: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """
        结合关键词和语义相似度搜索
        
        先做关键词过滤，再做向量相似度排序。
        """
        try:
            with SessionLocal() as db:
                import json
                
                if memory_type:
                    sql = text("""
                        SELECT 
                            me.id,
                            me.memory_id,
                            me.user_id,
                            me.memory_type,
                            me.created_at,
                            um.content,
                            um.context,
                            1 - (me.embedding <=> :embedding::vector) as similarity
                        FROM memory_embeddings me
                        JOIN user_memories um ON me.memory_id = um.id
                        WHERE me.user_id = :user_id
                            AND me.memory_type = :memory_type
                            AND um.content::text ILIKE :keyword
                        ORDER BY me.embedding <=> :embedding::vector
                        LIMIT :limit
                    """)
                    result = db.execute(sql, {
                        "embedding": query_embedding,
                        "user_id": user_id,
                        "memory_type": memory_type,
                        "keyword": f"%{keyword}%",
                        "limit": limit,
                    })
                else:
                    sql = text("""
                        SELECT 
                            me.id,
                            me.memory_id,
                            me.user_id,
                            me.memory_type,
                            me.created_at,
                            um.content,
                            um.context,
                            1 - (me.embedding <=> :embedding::vector) as similarity
                        FROM memory_embeddings me
                        JOIN user_memories um ON me.memory_id = um.id
                        WHERE me.user_id = :user_id
                            AND um.content::text ILIKE :keyword
                        ORDER BY me.embedding <=> :embedding::vector
                        LIMIT :limit
                    """)
                    result = db.execute(sql, {
                        "embedding": query_embedding,
                        "user_id": user_id,
                        "keyword": f"%{keyword}%",
                        "limit": limit,
                    })
                
                rows = result.fetchall()
                return [
                    {
                        "id": row[0],
                        "memory_id": row[1],
                        "user_id": row[2],
                        "memory_type": row[3],
                        "created_at": row[4].isoformat() if row[4] else None,
                        "content": row[5],
                        "context": row[6],
                        "similarity": float(row[7]) if row[7] else 0.0,
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []


# 全局实例
semantic_search_service = SemanticSearchService()
