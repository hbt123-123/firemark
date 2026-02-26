"""
Agent 记忆系统 - 长期记忆（用户历史）
"""
from datetime import date

from app.dependencies import SessionLocal
from app.models import UserMemory


class LongTermMemory:
    """长期记忆 - 存储用户的学习历史和偏好"""
    
    def __init__(self):
        pass
    
    def add_memory(
        self, 
        user_id: int, 
        memory_type: str, 
        content: str,
        metadata: dict | None = None
    ) -> int:
        """添加记忆"""
        with SessionLocal() as db:
            memory = UserMemory(
                user_id=user_id,
                memory_type=memory_type,
                content=content,
                metadata=metadata or {},
            )
            db.add(memory)
            db.commit()
            db.refresh(memory)
            return memory.id
    
    def get_recent_memories(self, user_id: int, limit: int = 10) -> list[dict]:
        """获取最近的记忆"""
        with SessionLocal() as db:
            memories = (
                db.query(UserMemory)
                .filter(UserMemory.user_id == user_id)
                .order_by(UserMemory.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": m.id,
                    "type": m.memory_type,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in memories
            ]
    
    def search_memories(self, user_id: int, keyword: str) -> list[dict]:
        """搜索记忆"""
        with SessionLocal() as db:
            memories = (
                db.query(UserMemory)
                .filter(
                    UserMemory.user_id == user_id,
                    UserMemory.content.contains(keyword)
                )
                .order_by(UserMemory.created_at.desc())
                .limit(20)
                .all()
            )
            return [
                {
                    "id": m.id,
                    "type": m.memory_type,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in memories
            ]
    
    def get_user_profile(self, user_id: int) -> dict:
        """获取用户画像"""
        memories = self.get_recent_memories(user_id, limit=50)
        
        # 简单聚合
        preferences = {}
        for memory in memories:
            if memory["type"] == "preference":
                preferences[memory["content"]] = True
        
        return {
            "recent_memories": memories[:10],
            "preferences": preferences,
            "total_memories": len(memories),
        }


# 全局实例
long_term_memory = LongTermMemory()
