from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

from app.dependencies import get_current_user, SessionLocal
from app.models import User, Goal
from app.utils.sanitize import sanitize_input


class GoalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: date
    end_date: date
    objective_topic: Optional[str] = None
    objective_criterion: Optional[str] = None
    objective_motivation: Optional[str] = None
    requirement_time: Optional[str] = None
    requirement_style: Optional[str] = None
    requirement_baseline: Optional[str] = None
    resource_preference: Optional[str] = None


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    current_phase: Optional[str] = None
    objective_topic: Optional[str] = None
    objective_criterion: Optional[str] = None


class GoalResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    start_date: date
    end_date: date
    outline: Optional[dict]
    status: str
    current_phase: Optional[str]
    objective_topic: Optional[str]
    objective_criterion: Optional[str]
    objective_motivation: Optional[str]
    requirement_time: Optional[str]
    requirement_style: Optional[str]
    requirement_baseline: Optional[str]
    resource_preference: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class GoalListResponse(BaseModel):
    goals: List[GoalResponse]
    total: int


router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_user),
):
    """创建新目标"""
    with SessionLocal() as db:
        if goal_data.end_date < goal_data.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )

        new_goal = Goal(
            user_id=current_user.id,
            title=sanitize_input(goal_data.title, max_length=200),
            description=sanitize_input(goal_data.description) if goal_data.description else None,
            start_date=goal_data.start_date,
            end_date=goal_data.end_date,
            objective_topic=goal_data.objective_topic,
            objective_criterion=goal_data.objective_criterion,
            objective_motivation=goal_data.objective_motivation,
            requirement_time=goal_data.requirement_time,
            requirement_style=goal_data.requirement_style,
            requirement_baseline=goal_data.requirement_baseline,
            resource_preference=goal_data.resource_preference,
            status="active",
        )
        db.add(new_goal)
        db.commit()
        db.refresh(new_goal)
        return new_goal


@router.get("", response_model=GoalListResponse)
async def get_goals(
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """获取用户的目标列表"""
    with SessionLocal() as db:
        query = db.query(Goal).filter(Goal.user_id == current_user.id)
        
        if status:
            query = query.filter(Goal.status == status)
        
        total = query.count()
        goals = query.order_by(Goal.created_at.desc()).offset(offset).limit(limit).all()
        
        return GoalListResponse(goals=goals, total=total)


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
):
    """获取目标详情"""
    with SessionLocal() as db:
        goal = db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.user_id == current_user.id
        ).first()
        
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )
        
        return goal


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: int,
    goal_data: GoalUpdate,
    current_user: User = Depends(get_current_user),
):
    """更新目标"""
    with SessionLocal() as db:
        goal = db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.user_id == current_user.id
        ).first()
        
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )
        
        if goal_data.title is not None:
            goal.title = sanitize_input(goal_data.title, max_length=200)
        if goal_data.description is not None:
            goal.description = sanitize_input(goal_data.description)
        if goal_data.status is not None:
            goal.status = goal_data.status
        if goal_data.current_phase is not None:
            goal.current_phase = goal_data.current_phase
        if goal_data.objective_topic is not None:
            goal.objective_topic = goal_data.objective_topic
        if goal_data.objective_criterion is not None:
            goal.objective_criterion = goal_data.objective_criterion
        
        db.commit()
        db.refresh(goal)
        return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
):
    """删除目标"""
    with SessionLocal() as db:
        goal = db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.user_id == current_user.id
        ).first()
        
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )
        
        db.delete(goal)
        db.commit()
        return None
