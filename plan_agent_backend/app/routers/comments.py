from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

from app.dependencies import get_current_user, SessionLocal
from app.models import User, Task, TaskComment
from app.utils.sanitize import sanitize_input
from app.utils.enums import CommentType


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, description="Comment content")
    type: str = Field(default="comment", description="Type: 'comment' or 'like'")

    @field_validator('content')
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        return sanitize_input(v, max_length=2000)

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in CommentType.valid_values():
            raise ValueError(f"Type must be one of: {CommentType.valid_values()}")
        return v


class CommentResponse(BaseModel):
    id: int
    task_id: int
    user_id: int
    username: str
    content: str
    type: str
    created_at: datetime

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    comments: List[CommentResponse]
    total: int
    task_id: int


router = APIRouter(tags=["comments"])


@router.get("/tasks/{task_id}/comments", response_model=CommentListResponse)
async def get_task_comments(
    task_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        task = (
            db.query(Task)
            .filter(Task.id == task_id)
            .first()
        )

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        comments = (
            db.query(TaskComment)
            .filter(TaskComment.task_id == task_id)
            .order_by(TaskComment.created_at.desc())
            .all()
        )

        result = []
        for comment in comments:
            user = db.query(User).filter(User.id == comment.user_id).first()
            result.append(CommentResponse(
                id=comment.id,
                task_id=comment.task_id,
                user_id=comment.user_id,
                username=user.username if user else "Unknown",
                content=comment.content,
                type=comment.type,
                created_at=comment.created_at,
            ))

        return CommentListResponse(
            comments=result,
            total=len(result),
            task_id=task_id,
        )


@router.post("/tasks/{task_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    task_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        task = (
            db.query(Task)
            .filter(Task.id == task_id)
            .first()
        )

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        if comment_data.type == CommentType.LIKE.value:
            existing_like = (
                db.query(TaskComment)
                .filter(
                    TaskComment.task_id == task_id,
                    TaskComment.user_id == current_user.id,
                    TaskComment.type == CommentType.LIKE.value,
                )
                .first()
            )

            if existing_like:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You have already liked this task",
                )

        new_comment = TaskComment(
            task_id=task_id,
            user_id=current_user.id,
            content=comment_data.content,
            type=comment_data.type,
        )
        db.add(new_comment)
        db.commit()
        db.refresh(new_comment)

        return CommentResponse(
            id=new_comment.id,
            task_id=new_comment.task_id,
            user_id=new_comment.user_id,
            username=current_user.username,
            content=new_comment.content,
            type=new_comment.type,
            created_at=new_comment.created_at,
        )


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        comment = (
            db.query(TaskComment)
            .filter(
                TaskComment.id == comment_id,
                TaskComment.user_id == current_user.id,
            )
            .first()
        )

        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found or you don't have permission to delete it",
            )

        db.delete(comment)
        db.commit()

        return {"success": True, "message": "Comment deleted"}


@router.get("/tasks/{task_id}/likes")
async def get_task_likes(
    task_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        task = (
            db.query(Task)
            .filter(Task.id == task_id)
            .first()
        )

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        likes = (
            db.query(TaskComment)
            .filter(
                TaskComment.task_id == task_id,
                TaskComment.type == CommentType.LIKE.value,
            )
            .all()
        )

        user_likes = []
        for like in likes:
            user = db.query(User).filter(User.id == like.user_id).first()
            if user:
                user_likes.append({
                    "user_id": user.id,
                    "username": user.username,
                })

        return {
            "task_id": task_id,
            "total_likes": len(likes),
            "liked_by": user_likes,
            "has_liked": any(like.user_id == current_user.id for like in likes),
        }


@router.post("/tasks/{task_id}/like")
async def toggle_like(
    task_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        task = (
            db.query(Task)
            .filter(Task.id == task_id)
            .first()
        )

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        existing_like = (
            db.query(TaskComment)
            .filter(
                TaskComment.task_id == task_id,
                TaskComment.user_id == current_user.id,
                TaskComment.type == CommentType.LIKE.value,
            )
            .first()
        )

        if existing_like:
            db.delete(existing_like)
            db.commit()
            return {
                "success": True,
                "action": "unliked",
                "message": "Like removed",
            }
        else:
            new_like = TaskComment(
                task_id=task_id,
                user_id=current_user.id,
                content="",
                type=CommentType.LIKE.value,
            )
            db.add(new_like)
            db.commit()
            return {
                "success": True,
                "action": "liked",
                "message": "Task liked",
            }
