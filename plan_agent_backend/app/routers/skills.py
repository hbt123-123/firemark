"""
Skills Router - 技能路由

迁移到 app/agent/，此文件保留用于向后兼容
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any, Optional

from app.dependencies import get_current_user
from app.models import User
from app.agent.registry import plugin_registry


class SkillExecuteRequest(BaseModel):
    skill_name: str = Field(..., description="Name of the skill to execute")
    parameters: dict = Field(default_factory=dict, description="Parameters for the skill")


class SkillExecuteResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Optional[dict] = None


router = APIRouter(prefix="/skills", tags=["skills"])


@router.post("/execute", response_model=SkillExecuteResponse)
async def execute_skill(
    request: SkillExecuteRequest,
    current_user: User = Depends(get_current_user),
):
    skill = plugin_registry.get_skill(request.skill_name)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{request.skill_name}' not found",
        )
    
    result = await skill.execute(
        parameters=request.parameters,
        user_id=current_user.id,
    )
    
    return SkillExecuteResponse(
        success=result.success,
        data=result.data,
        error=result.error,
        metadata=result.metadata,
    )


@router.get("/list")
async def list_skills():
    return {"skills": plugin_registry.list_skills()}
