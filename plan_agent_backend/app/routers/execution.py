from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

from app.dependencies import get_current_user
from app.models import User, ExecutionLog
from app.services.execution_service import execution_service


class ExecutionLogResponse(BaseModel):
    id: int
    user_id: int
    log_date: date
    tasks_completed: int
    tasks_total: int
    difficulties: Optional[str] = None
    feedback: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExecutionStatsResponse(BaseModel):
    total_days: int
    total_tasks: int
    total_completed: int
    average_completion_rate: float
    streak_days: int


class UpdateFeedbackRequest(BaseModel):
    difficulties: Optional[str] = Field(None, description="Difficulties encountered")
    feedback: Optional[str] = Field(None, description="Additional feedback")


router = APIRouter(prefix="/execution", tags=["execution"])


@router.get("/logs", response_model=list[ExecutionLogResponse])
async def get_execution_logs(
    start_date: date | None = Query(None, description="Start date filter"),
    end_date: date | None = Query(None, description="End date filter"),
    current_user: User = Depends(get_current_user),
):
    logs = execution_service.get_execution_logs(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )
    return logs


@router.get("/logs/{log_date}", response_model=ExecutionLogResponse)
async def get_execution_log_by_date(
    log_date: date,
    current_user: User = Depends(get_current_user),
):
    log = execution_service.get_execution_log(
        user_id=current_user.id,
        log_date=log_date,
    )
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution log not found for this date",
        )
    return log


@router.get("/stats", response_model=ExecutionStatsResponse)
async def get_execution_stats(
    start_date: date | None = Query(None, description="Start date filter"),
    end_date: date | None = Query(None, description="End date filter"),
    current_user: User = Depends(get_current_user),
):
    stats = execution_service.get_execution_stats(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )
    return stats


@router.post("/logs/{log_date}/feedback", response_model=ExecutionLogResponse)
async def update_execution_feedback(
    log_date: date,
    request: UpdateFeedbackRequest,
    current_user: User = Depends(get_current_user),
):
    log = execution_service.update_execution_feedback(
        user_id=current_user.id,
        log_date=log_date,
        difficulties=request.difficulties,
        feedback=request.feedback,
    )
    return log


@router.post("/logs/generate")
async def generate_daily_log(
    log_date: date = Query(..., description="Date to generate log for"),
    current_user: User = Depends(get_current_user),
):
    log = execution_service.log_daily_execution(
        user_id=current_user.id,
        log_date=log_date,
    )
    return {
        "success": True,
        "log_id": log.id,
        "tasks_completed": log.tasks_completed,
        "tasks_total": log.tasks_total,
    }
