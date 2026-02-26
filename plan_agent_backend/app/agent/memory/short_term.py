"""
Agent 记忆系统 - 短期记忆（对话上下文）
"""
from typing import Any
from app.agent.types import Message, ConversationContext


class ShortTermMemory:
    """短期记忆 - 当前会话的对话上下文"""
    
    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self._sessions: dict[str, ConversationContext] = {}
    
    def create_session(self, session_id: str, user_id: int) -> ConversationContext:
        """创建新会话"""
        ctx = ConversationContext(session_id=session_id, user_id=user_id)
        self._sessions[session_id] = ctx
        return ctx
    
    def get_session(self, session_id: str) -> ConversationContext | None:
        """获取会话"""
        return self._sessions.get(session_id)
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """添加消息"""
        ctx = self._sessions.get(session_id)
        if not ctx:
            return
        
        msg = Message(role=role, content=content)
        ctx.messages.append(msg)
        
        # 限制消息数量
        if len(ctx.messages) > self.max_messages:
            self._sessions[session_id].messages = self._sessions[session_id].messages[-self.max_messages:]
    
    def update_state(self, session_id: str, state: str) -> None:
        """更新状态"""
        ctx = self._sessions.get(session_id)
        if ctx:
            ctx.state = state
    
    def collect_info(self, session_id: str, key: str, value: Any) -> None:
        """收集信息"""
        ctx = self._sessions.get(session_id)
        if ctx:
            ctx.collected_info[key] = value
    
    def get_context_for_llm(self, session_id: str) -> list[dict]:
        """获取用于 LLM 的上下文"""
        ctx = self._sessions.get(session_id)
        if not ctx:
            return []
        
        # 转换为消息格式
        messages = [{"role": "system", "content": "你是学习助手"}]
        
        for msg in ctx.messages[-10:]:  # 最近 10 条
            messages.append({
                "role": msg.role.value if hasattr(msg.role, 'value') else msg.role,
                "content": msg.content,
            })
        
        return messages
    
    def clear_session(self, session_id: str) -> None:
        """清除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]


# 全局实例
short_term_memory = ShortTermMemory()
