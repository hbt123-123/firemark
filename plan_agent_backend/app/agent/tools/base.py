"""
Agent Tools 基类
"""
from abc import ABC, abstractmethod
from typing import Any

from app.agent.types import ToolResult


class BaseTool(ABC):
    """Tool 基类"""
    
    name: str
    description: str
    input_schema: dict
    output_schema: dict
    
    @abstractmethod
    async def execute(self, parameters: dict, user_id: int | None = None) -> ToolResult:
        """执行 Tool"""
        pass
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
        }
