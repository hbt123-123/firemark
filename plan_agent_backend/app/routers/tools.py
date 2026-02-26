"""
Tools Router - 工具路由

迁移到 app/agent/，此文件保留用于向后兼容
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any, Optional

from app.dependencies import get_current_user
from app.models import User
from app.agent.registry import plugin_registry


class ToolExecuteRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: dict = Field(default_factory=dict, description="Parameters for the tool")


class ToolExecuteResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None


router = APIRouter(prefix="/tools", tags=["tools"])


@router.post("/execute", response_model=ToolExecuteResponse)
async def execute_tool(
    request: ToolExecuteRequest,
    current_user: User = Depends(get_current_user),
):
    tool = plugin_registry.get_tool(request.tool_name)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{request.tool_name}' not found",
        )
    
    result = await tool.execute(
        parameters=request.parameters,
        user_id=current_user.id,
    )
    
    return ToolExecuteResponse(
        success=result.success,
        data=result.data,
        error=result.error,
    )


@router.get("/list")
async def list_tools():
    return {"tools": plugin_registry.list_tools()}
