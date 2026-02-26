from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

from app.dependencies import get_current_user
from app.models import User, ReflectionLog
from app.services.reflection_service import reflection_service


class ReflectionRequest(BaseModel):
    goal_id: Optional[int] = Field(None, description="Goal ID to reflect on (optional)")
    auto_apply: bool = Field(True, description="Whether to auto-apply adjustments")


class ReflectionLogResponse(BaseModel):
    id: int
    user_id: int
    goal_id: Optional[int] = None
    reflection_time: datetime
    analysis: str
    adjustment_plan: dict
    applied: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ReflectionResultResponse(BaseModel):
    success: bool
    reflection_log_id: int
    analysis: dict
    recommendations: dict
    summary: str
    applied: bool
    apply_result: Optional[dict] = None


router = APIRouter(prefix="/reflection", tags=["reflection"])


@router.post("/run", response_model=ReflectionResultResponse)
async def run_reflection(
    request: ReflectionRequest,
    current_user: User = Depends(get_current_user),
):
    result = await reflection_service.run_reflection(
        user_id=current_user.id,
        goal_id=request.goal_id,
        auto_apply=request.auto_apply,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Reflection failed"),
        )

    return result


@router.get("/logs", response_model=List[ReflectionLogResponse])
async def get_reflection_logs(
    goal_id: Optional[int] = Query(None, description="Filter by goal ID"),
    limit: int = Query(10, ge=1, le=50, description="Number of logs to return"),
    current_user: User = Depends(get_current_user),
):
    logs = reflection_service.get_reflection_logs(
        user_id=current_user.id,
        goal_id=goal_id,
        limit=limit,
    )
    return logs


@router.get("/logs/{log_id}", response_model=ReflectionLogResponse)
async def get_reflection_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
):
    from app.dependencies import SessionLocal

    with SessionLocal() as db:
        log = (
            db.query(ReflectionLog)
            .filter(
                ReflectionLog.id == log_id,
                ReflectionLog.user_id == current_user.id,
            )
            .first()
        )

        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reflection log not found",
            )

        return log


@router.post("/logs/{log_id}/apply")
async def apply_reflection_adjustments(
    log_id: int,
    current_user: User = Depends(get_current_user),
):
    from app.dependencies import SessionLocal

    with SessionLocal() as db:
        log = (
            db.query(ReflectionLog)
            .filter(
                ReflectionLog.id == log_id,
                ReflectionLog.user_id == current_user.id,
            )
            .first()
        )

        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reflection log not found",
            )

        if log.applied:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This reflection has already been applied",
            )

        recommendations = log.adjust_plan.get("recommendations", {})

        apply_result = await reflection_service.apply_adjustments(
            user_id=current_user.id,
            goal_id=log.goal_id,
            recommendations=recommendations,
        )

        log.applied = True
        db.commit()

        return {
            "success": True,
            "message": "Adjustments applied successfully",
            "apply_result": apply_result,
        }
