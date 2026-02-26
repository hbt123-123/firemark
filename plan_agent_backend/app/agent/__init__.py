"""
Agent 模块 - 智能体核心

提供插件化的 Skills/Tools 管理和 LLM-driven 的智能对话能力。
"""
from app.agent.base import Agent, AgentConfig
from app.agent.registry import AgentRegistry, agent_registry
from app.agent.types import Message, Role, ToolCall, ToolResult, SkillResult

# 导出便捷函数
def get_agent(name: str = "default") -> Agent:
    """获取 Agent 实例"""
    return agent_registry.get_agent(name)


__all__ = [
    "Agent",
    "AgentConfig",
    "AgentRegistry", 
    "agent_registry",
    "Message",
    "Role",
    "ToolCall", 
    "ToolResult",
    "SkillResult",
    "get_agent",
]
