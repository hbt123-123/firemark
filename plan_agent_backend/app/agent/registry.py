"""
Plugin 插件注册表 - 支持 Skills 和 Tools 统一管理
"""
import importlib
import inspect
import logging
from pathlib import Path
from typing import Any, Callable, Optional

from app.agent.skills.base import BaseSkill
from app.agent.tools.base import BaseTool

logger = logging.getLogger(__name__)


class PluginRegistry:
    """插件注册表 - 统一管理 Skills 和 Tools"""
    
    _instance: Optional["PluginRegistry"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._skills: dict[str, BaseSkill] = {}
        self._tools: dict[str, BaseTool] = {}
        self._skill_decorators: list[Callable] = []
        self._tool_decorators: list[Callable] = []
        self._initialized = True
    
    # ========== Skill 管理 ==========
    
    def register_skill(self, skill: BaseSkill) -> None:
        """注册 Skill"""
        if skill.name in self._skills:
            raise ValueError(f"Skill '{skill.name}' is already registered")
        self._skills[skill.name] = skill
        logger.info(f"Registered skill: {skill.name}")
    
    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """获取 Skill"""
        return self._skills.get(name)
    
    def list_skills(self) -> list[dict]:
        """列出所有 Skills"""
        return [skill.to_dict() for skill in self._skills.values()]
    
    def unregister_skill(self, name: str) -> bool:
        """注销 Skill"""
        if name in self._skills:
            del self._skills[name]
            return True
        return False
    
    # ========== Tool 管理 ==========
    
    def register_tool(self, tool: BaseTool) -> None:
        """注册 Tool"""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取 Tool"""
        return self._tools.get(name)
    
    def list_tools(self) -> list[dict]:
        """列出所有 Tools"""
        return [tool.to_dict() for tool in self._tools.values()]
    
    def unregister_tool(self, name: str) -> bool:
        """注销 Tool"""
        if name in self._tools:
            del self._tools[name]
            return True
        return False
    
    # ========== 便捷方法 ==========
    
    def get_all_tools_for_llm(self) -> str:
        """获取所有工具描述（用于 LLM）"""
        lines = ["Available tools:"]
        for tool in self._tools.values():
            lines.append(f"- {tool.name}: {tool.description}")
            if tool.input_schema.get("properties"):
                lines.append(f"  Parameters: {list(tool.input_schema['properties'].keys())}")
        return "\n".join(lines)
    
    def get_tools_descriptions(self) -> list[dict]:
        """获取工具描述列表"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                }
            }
            for tool in self._tools.values()
        ]


# 全局注册表实例
plugin_registry = PluginRegistry()


# ========== 装饰器 ==========

def register_skill(skill_class: type[BaseSkill]) -> type[BaseSkill]:
    """注册 Skill 的装饰器"""
    plugin_registry._skill_decorators.append(skill_class)
    return skill_class


def register_tool(tool_class: type[BaseTool]) -> type[BaseTool]:
    """注册 Tool 的装饰器"""
    plugin_registry._tool_decorators.append(tool_class)
    return tool_class


# ========== 自动发现 ==========

async def discover_plugins(skills_dir: str | Path = None, tools_dir: str | Path = None) -> None:
    """
    自动发现并加载插件
    
    扫描指定目录下的模块，自动注册 Skills 和 Tools
    """
    from app.agent import skills as skills_module
    from app.agent import tools as tools_module
    
    # 扫描 Skills
    skills_path = Path(skills_module.__file__).parent
    await _scan_and_register(skills_path, BaseSkill, plugin_registry.register_skill)
    
    # 扫描 Tools
    tools_path = Path(tools_module.__file__).parent
    await _scan_and_register(tools_path, BaseTool, plugin_registry.register_tool)
    
    logger.info(f"Discovered {len(plugin_registry._skills)} skills and {len(plugin_registry._tools)} tools")


async def _scan_and_register(
    path: Path,
    base_class: type[BaseSkill] | type[BaseTool],
    register_func: Callable
) -> None:
    """扫描目录并注册插件"""
    for file in path.glob("*.py"):
        if file.name.startswith("_") or file.name.startswith("base"):
            continue
        
        module_name = file.stem
        try:
            # 动态导入模块
            if "skills" in str(path):
                module = importlib.import_module(f"app.agent.skills.{module_name}")
            else:
                module = importlib.import_module(f"app.agent.tools.{module_name}")
            
            # 查找模块中的插件类
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, base_class) and obj is not base_class:
                    # 实例化并注册
                    instance = obj()
                    register_func(instance)
                    logger.debug(f"Auto-registered: {name}")
                    
        except Exception as e:
            logger.warning(f"Failed to load {module_name}: {e}")


# ========== 兼容旧代码 ==========

# 提供旧的接口别名
skill_registry = plugin_registry
tool_registry = plugin_registry
