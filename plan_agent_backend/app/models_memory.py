"""
PostgreSQL 向量记忆模型

使用 pgvector 扩展存储记忆的向量嵌入。
"""
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, User, UserMemory


class MemoryEmbedding(Base):
    """
    记忆向量存储表
    
    存储用户记忆的向量表示，支持语义相似度搜索。
    """
    __tablename__ = "memory_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    memory_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("user_memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 向量存储为字节 (pgvector 的 vector(1536))
    embedding: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    
    # 用于快速过滤
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now()
    )

    # 关系
    memory: Mapped["UserMemory"] = relationship("UserMemory", foreign_keys=[memory_id])

    __table_args__ = (
        # 用户 + 类型的复合索引
        Index("ix_memory_embeddings_user_type", "user_id", "memory_type"),
        # 向量相似度搜索辅助索引
        Index("ix_memory_embeddings_user_created", "user_id", "created_at"),
    )
