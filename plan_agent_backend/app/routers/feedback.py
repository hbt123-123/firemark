from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User, WordFeedback
from app.schemas import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    request: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交功能反馈"""
    feedback = WordFeedback(
        user_id=current_user.id,
        feature_name=request.feature_name,
        feedback_type=request.feedback_type,
        content=request.content,
        rating=request.rating,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return FeedbackResponse(success=True, id=feedback.id)
