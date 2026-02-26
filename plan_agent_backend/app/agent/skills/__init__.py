"""
Agent Skills - 业务技能模块

所有 Skills 在此目录下定义，使用 @register_skill 装饰器自动注册
"""
from app.agent.skills.base import BaseSkill

# 延迟导入避免循环依赖
plugin_registry = None

def __getattr__(name):
    global plugin_registry
    if name == "plugin_registry":
        from app.agent.registry import plugin_registry
        return plugin_registry
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["BaseSkill", "plugin_registry"]
