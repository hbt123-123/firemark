"""
Agent 模块 - 智能体核心

提供插件化的 Skills/Tools 管理和 LLM-driven 的智能对话能力。
"""

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

def __getattr__(name):
    if name in ("Agent", "AgentConfig"):
        from app.agent.base import Agent, AgentConfig
        return Agent if name == "Agent" else AgentConfig
    elif name in ("AgentRegistry", "agent_registry"):
        from app.agent.registry import AgentRegistry, agent_registry
        return agent_registry if name == "agent_registry" else AgentRegistry
    elif name in ("Message", "Role", "ToolCall", "ToolResult", "SkillResult"):
        from app.agent.types import Message, Role, ToolCall, ToolResult, SkillResult
        mapping = {
            "Message": Message,
            "Role": Role,
            "ToolCall": ToolCall,
            "ToolResult": ToolResult,
            "SkillResult": SkillResult,
        }
        return mapping[name]
    elif name == "get_agent":
        def get_agent(name: str = "default"):
            from app.agent.base import Agent
            return Agent(name)
        return get_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
