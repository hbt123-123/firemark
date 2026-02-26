"""
Agent Tools - 工具模块

所有 Tools 在此目录下定义，使用 @register_tool 装饰器自动注册
"""
from app.agent.tools.base import BaseTool

# 延迟导入避免循环依赖
plugin_registry = None

def __getattr__(name):
    global plugin_registry
    if name == "plugin_registry":
        from app.agent.registry import plugin_registry
        return plugin_registry
    if name == "register_tool":
        from app.agent.registry import register_tool
        return register_tool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["BaseTool", "register_tool", "plugin_registry"]
