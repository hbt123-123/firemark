from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime

from app.dependencies import get_current_user, SessionLocal
from app.models import User, Task, Goal
from app.schemas import TaskCreate, TaskUpdate, TaskInDB
from app.services.execution_service import execution_service
from app.utils.enums import TaskStatus, TaskPriority
from app.utils.sanitize import sanitize_input


class TaskResponse(BaseModel):
    id: int
    user_id: int
    goal_id: Optional[int] = None
    fixed_schedule_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    due_date: date
    due_time: Optional[str] = None
    status: str
    priority: int
    dependencies: Optional[List[int]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int


class TaskStatusUpdate(BaseModel):
    status: str

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        if not TaskStatus.is_valid(v):
            raise ValueError(f"Invalid status. Must be one of: {TaskStatus.valid_values()}")
        return v


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        new_task = Task(
            user_id=current_user.id,
            goal_id=task_data.goal_id,
            fixed_schedule_id=task_data.fixed_schedule_id,
            title=sanitize_input(task_data.title, max_length=200),
            description=sanitize_input(task_data.description) if task_data.description else None,
            due_date=task_data.due_date,
            due_time=task_data.due_time,
            status=TaskStatus.PENDING.value,
            priority=task_data.priority if TaskPriority.is_valid(task_data.priority) else TaskPriority.MEDIUM.value,
            dependencies=task_data.dependencies,
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        execution_service.log_daily_execution(
            user_id=current_user.id,
            log_date=task_data.due_date,
        )

        return new_task


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    due_date: Optional[date] = Query(None, description="Filter by due date"),
    goal_id: Optional[int] = Query(None, description="Filter by goal ID"),
    priority: Optional[int] = Query(None, description="Filter by priority"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    if status_filter and not TaskStatus.is_valid(status_filter):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {TaskStatus.valid_values()}",
        )

    with SessionLocal() as db:
        query = db.query(Task).filter(Task.user_id == current_user.id)

        if status_filter:
            query = query.filter(Task.status == status_filter)
        if due_date:
            query = query.filter(Task.due_date == due_date)
        if goal_id:
            query = query.filter(Task.goal_id == goal_id)
        if priority is not None:
            query = query.filter(Task.priority == priority)

        total = query.count()
        tasks = query.order_by(Task.due_date, Task.due_time).offset(skip).limit(limit).all()

        return TaskListResponse(tasks=tasks, total=total)


@router.get("/today", response_model=TaskListResponse)
async def get_today_tasks(
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    with SessionLocal() as db:
        tasks = (
            db.query(Task)
            .filter(
                Task.user_id == current_user.id,
                Task.due_date == today,
            )
            .order_by(Task.due_time)
            .all()
        )
        return TaskListResponse(tasks=tasks, total=len(tasks))


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        task = (
            db.query(Task)
            .filter(Task.id == task_id, Task.user_id == current_user.id)
            .first()
        )
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        task = (
            db.query(Task)
            .filter(Task.id == task_id, Task.user_id == current_user.id)
            .first()
        )
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        old_status = task.status
        old_due_date = task.due_date

        update_data = task_data.model_dump(exclude_unset=True)

        if "status" in update_data and not TaskStatus.is_valid(update_data["status"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {TaskStatus.valid_values()}",
            )

        if "priority" in update_data and not TaskPriority.is_valid(update_data["priority"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority. Must be one of: {TaskPriority.valid_values()}",
            )

        for field, value in update_data.items():
            if field in ["title", "description"] and value:
                value = sanitize_input(value, max_length=200 if field == "title" else None)
            setattr(task, field, value)

        db.commit()
        db.refresh(task)

        if "status" in update_data or "due_date" in update_data:
            dates_to_update = set()
            if old_due_date:
                dates_to_update.add(old_due_date)
            if task.due_date:
                dates_to_update.add(task.due_date)

            for log_date in dates_to_update:
                execution_service.log_daily_execution(
                    user_id=current_user.id,
                    log_date=log_date,
                )

        return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        task = (
            db.query(Task)
            .filter(Task.id == task_id, Task.user_id == current_user.id)
            .first()
        )
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        due_date = task.due_date
        db.delete(task)
        db.commit()

        execution_service.log_daily_execution(
            user_id=current_user.id,
            log_date=due_date,
        )

        return {"success": True, "message": "Task deleted"}


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        task = (
            db.query(Task)
            .filter(Task.id == task_id, Task.user_id == current_user.id)
            .first()
        )
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        task.status = TaskStatus.COMPLETED.value
        db.commit()
        db.refresh(task)

        execution_service.log_daily_execution(
            user_id=current_user.id,
            log_date=task.due_date,
        )

        return task


@router.post("/{task_id}/skip", response_model=TaskResponse)
async def skip_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        task = (
            db.query(Task)
            .filter(Task.id == task_id, Task.user_id == current_user.id)
            .first()
        )
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        task.status = TaskStatus.SKIPPED.value
        db.commit()
        db.refresh(task)

        execution_service.log_daily_execution(
            user_id=current_user.id,
            log_date=task.due_date,
        )

        return task


@router.post("/batch-update-status")
async def batch_update_status(
    task_ids: List[int],
    new_status: str = Query(..., description="New status"),
    current_user: User = Depends(get_current_user),
):
    if not TaskStatus.is_valid(new_status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {TaskStatus.valid_values()}",
        )

    with SessionLocal() as db:
        tasks = (
            db.query(Task)
            .filter(
                Task.id.in_(task_ids),
                Task.user_id == current_user.id,
            )
            .all()
        )

        dates_to_update = set()
        for task in tasks:
            dates_to_update.add(task.due_date)
            task.status = new_status

        db.commit()

        for log_date in dates_to_update:
            execution_service.log_daily_execution(
                user_id=current_user.id,
                log_date=log_date,
            )

        return {
            "success": True,
            "updated_count": len(tasks),
            "message": f"Updated {len(tasks)} tasks to {new_status}",
        }
