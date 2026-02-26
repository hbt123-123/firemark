"""
Agent 共用类型定义
"""
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class Role(str, Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    """对话消息"""
    role: Role
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    """工具调用请求"""
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    tool_call_id: Optional[str] = None


class SkillResult(BaseModel):
    """Skill 执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntentType(str, Enum):
    """意图类型"""
    CREATE_PLAN = "create_plan"
    ADJUST_PLAN = "adjust_plan"
    ASK_QUESTION = "ask_question"
    UPDATE_TASK = "update_task"
    VIEW_PROGRESS = "view_progress"
    CLARIFICATION = "clarification"
    CHAT = "chat"
    UNKNOWN = "unknown"


class Intent(BaseModel):
    """识别到的意图"""
    type: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    entities: dict[str, Any] = Field(default_factory=dict)
    raw_response: Optional[str] = None


class Decision(BaseModel):
    """Agent 决策"""
    response: Optional[str] = None
    needs_tool: bool = False
    tool_calls: list[ToolCall] = Field(default_factory=list)
    next_state: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationContext(BaseModel):
    """对话上下文"""
    session_id: str
    user_id: int
    state: str = "idle"
    collected_info: dict[str, Any] = Field(default_factory=dict)
    messages: list[Message] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
