from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime

from app.dependencies import get_current_user, SessionLocal
from app.models import User


class PushTokenRequest(BaseModel):
    push_token: str = Field(..., min_length=1, max_length=255, description="Push notification token")


class UserResponse(BaseModel):
    id: int
    username: str
    push_token: str | None
    preferences: dict | None
    created_at: datetime

    class Config:
        from_attributes = True


class PreferencesUpdate(BaseModel):
    preferences: dict = Field(..., description="User preferences")


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/push-token")
async def update_push_token(
    request: PushTokenRequest,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == current_user.id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.push_token = request.push_token
        db.commit()

        return {
            "success": True,
            "message": "Push token updated successfully",
        }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == current_user.id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return UserResponse(
            id=user.id,
            username=user.username,
            push_token=user.push_token,
            preferences=user.preferences,
            created_at=user.created_at,
        )


@router.put("/preferences")
async def update_preferences(
    request: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == current_user.id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.preferences = request.preferences
        db.commit()

        return {
            "success": True,
            "message": "Preferences updated successfully",
            "preferences": request.preferences,
        }


@router.delete("/push-token")
async def remove_push_token(
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == current_user.id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.push_token = None
        db.commit()

        return {
            "success": True,
            "message": "Push token removed successfully",
        }
