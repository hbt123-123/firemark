"""
Agent Skills - 业务技能模块

所有 Skills 在此目录下定义，使用 @register_skill 装饰器自动注册
"""
from app.agent.skills.base import BaseSkill
from app.agent.registry import plugin_registry, register_skill

__all__ = ["BaseSkill", "register_skill", "plugin_registry"]
