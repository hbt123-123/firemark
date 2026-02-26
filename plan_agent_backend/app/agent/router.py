"""
Agent Router - 智能体 API 路由
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional

from app.dependencies import get_current_user
from app.models import User
from app.agent.base import default_agent


router = APIRouter(prefix="/agent", tags=["agent"])


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field(None, description="会话 ID")


class ChatResponse(BaseModel):
    """聊天响应"""
    success: bool
    response: str
    session_id: str
    intent: Optional[str] = None
    entities: Optional[dict] = None


class ExecuteSkillRequest(BaseModel):
    """执行 Skill 请求"""
    skill_name: str = Field(..., description="Skill 名称")
    parameters: dict = Field(default_factory=dict, description="Skill 参数")


class ListPluginsResponse(BaseModel):
    """插件列表响应"""
    skills: list[dict]
    tools: list[dict]


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    智能对话接口
    
    发送用户消息，获取 AI 智能回复。
    支持意图识别、工具调用、记忆管理。
    """
    try:
        result = await default_agent.chat(
            user_id=current_user.id,
            message=request.message,
            session_id=request.session_id,
        )
        
        return ChatResponse(
            success=True,
            response=result["response"],
            session_id=result["session_id"],
            intent=result.get("intent"),
            entities=result.get("entities"),
        )
    except Exception as e:
        return ChatResponse(
            success=False,
            response=f"处理消息时出错：{str(e)}",
            session_id=request.session_id or "",
        )


@router.post("/skill", response_model=dict)
async def execute_skill(
    request: ExecuteSkillRequest,
    current_user: User = Depends(get_current_user),
):
    """
    直接执行 Skill
    
    指定 Skill 名称和参数，直接执行并返回结果。
    """
    result = await default_agent.execute_skill(
        skill_name=request.skill_name,
        parameters=request.parameters,
        user_id=current_user.id,
    )
    
    return result


@router.get("/plugins", response_model=ListPluginsResponse)
async def list_plugins():
    """
    获取可用插件列表
    
    返回所有已注册的 Skills 和 Tools。
    """
    return ListPluginsResponse(
        skills=default_agent.get_skills(),
        tools=default_agent.get_tools(),
    )


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """清除会话"""
    from app.agent.memory import short_term_memory
    short_term_memory.clear_session(session_id)
    return {"success": True, "message": f"Session {session_id} cleared"}
