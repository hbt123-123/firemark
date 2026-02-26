from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime

from app.dependencies import get_current_user
from app.models import User
from app.services.ai_service import ai_dialogue_manager, DialogueState


class StartPlanRequest(BaseModel):
    initial_input: Optional[str] = Field(None, description="Initial user input")


class ContinuePlanRequest(BaseModel):
    session_id: int = Field(..., description="Session ID")
    answer: str = Field(..., description="User's answer to the current question")


class ConfirmPlanRequest(BaseModel):
    session_id: int = Field(..., description="Session ID")


class QuestionResponse(BaseModel):
    question_id: Optional[str] = None
    question: Optional[str] = None
    placeholder: Optional[str] = None
    progress: Optional[dict] = None
    section_title: Optional[str] = None
    section_description: Optional[str] = None
    state: str
    is_complete: bool = False


class PlanPreviewResponse(BaseModel):
    goal: dict
    outline: dict
    preview_tasks: list
    summary: str
    session_id: int


class SessionResponse(BaseModel):
    session_id: int
    state: str
    created_at: datetime


class ConfirmPlanResponse(BaseModel):
    success: bool
    goal_id: int
    tasks_created: int
    message: str


router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/start-plan", response_model=SessionResponse)
async def start_plan(
    request: StartPlanRequest,
    current_user: User = Depends(get_current_user),
):
    session = ai_dialogue_manager.create_session(
        user_id=current_user.id,
        initial_input=request.initial_input,
    )

    return SessionResponse(
        session_id=session.id,
        state=session.state,
        created_at=session.created_at,
    )


@router.post("/continue-plan")
async def continue_plan(
    request: ContinuePlanRequest,
    current_user: User = Depends(get_current_user),
):
    session = ai_dialogue_manager.get_session(request.session_id, current_user.id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied",
        )

    current_state = DialogueState(session.state)
    session_data = session.data or {}

    if current_state == DialogueState.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This session has already been completed",
        )

    if current_state == DialogueState.AWAITING_CONFIRMATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is awaiting confirmation. Use /confirm-plan endpoint.",
        )

    updated_data = await ai_dialogue_manager.process_answer(
        current_state, request.answer, session_data
    )

    new_state = DialogueState(updated_data.get("state", current_state.value))

    if new_state == DialogueState.AWAITING_CONFIRMATION:
        preview = await ai_dialogue_manager.generate_plan_preview(updated_data)
        updated_data["preview"] = preview
        ai_dialogue_manager.update_session(session, updated_data)

        return {
            "state": new_state.value,
            "is_complete": False,
            "is_awaiting_confirmation": True,
            "preview": PlanPreviewResponse(
                goal=preview.get("goal", {}),
                outline=preview.get("outline", {}),
                preview_tasks=preview.get("preview_tasks", []),
                summary=preview.get("summary", ""),
                session_id=session.id,
            ),
        }

    ai_dialogue_manager.update_session(session, updated_data)

    current_question = ai_dialogue_manager.get_current_question(new_state, updated_data)

    if current_question:
        return QuestionResponse(
            question_id=current_question.get("question_id"),
            question=current_question.get("question"),
            placeholder=current_question.get("placeholder"),
            progress=current_question.get("progress"),
            section_title=current_question.get("section_title"),
            section_description=current_question.get("section_description"),
            state=new_state.value,
            is_complete=False,
        )

    return QuestionResponse(
        state=new_state.value,
        is_complete=False,
    )


@router.get("/session/{session_id}")
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
):
    session = ai_dialogue_manager.get_session(session_id, current_user.id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied",
        )

    current_state = DialogueState(session.state)
    session_data = session.data or {}

    if current_state == DialogueState.AWAITING_CONFIRMATION:
        preview = session_data.get("preview", {})
        return {
            "state": current_state.value,
            "is_awaiting_confirmation": True,
            "preview": preview,
        }

    current_question = ai_dialogue_manager.get_current_question(current_state, session_data)

    if current_question:
        return QuestionResponse(
            question_id=current_question.get("question_id"),
            question=current_question.get("question"),
            placeholder=current_question.get("placeholder"),
            progress=current_question.get("progress"),
            section_title=current_question.get("section_title"),
            section_description=current_question.get("section_description"),
            state=current_state.value,
            is_complete=False,
        )

    return QuestionResponse(
        state=current_state.value,
        is_complete=current_state == DialogueState.COMPLETED,
    )


@router.post("/confirm-plan", response_model=ConfirmPlanResponse)
async def confirm_plan(
    request: ConfirmPlanRequest,
    current_user: User = Depends(get_current_user),
):
    session = ai_dialogue_manager.get_session(request.session_id, current_user.id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied",
        )

    current_state = DialogueState(session.state)
    
    if current_state != DialogueState.AWAITING_CONFIRMATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not in confirmation state",
        )

    session_data = session.data or {}
    preview = session_data.get("preview", {})

    if not preview:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No plan preview found in session",
        )

    goal = ai_dialogue_manager.create_goal_from_preview(
        user_id=current_user.id,
        preview=preview,
    )

    preview_tasks = preview.get("preview_tasks", [])
    tasks = ai_dialogue_manager.create_tasks_from_preview(
        goal_id=goal.id,
        user_id=current_user.id,
        preview_tasks=preview_tasks,
    )

    ai_dialogue_manager.complete_session(session.id)

    return ConfirmPlanResponse(
        success=True,
        goal_id=goal.id,
        tasks_created=len(tasks),
        message=f"Plan created successfully with {len(tasks)} tasks",
    )


@router.delete("/session/{session_id}")
async def cancel_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
):
    session = ai_dialogue_manager.get_session(session_id, current_user.id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied",
        )

    from app.dependencies import SessionLocal
    from app.models import AISession

    with SessionLocal() as db:
        db_session = db.query(AISession).filter(AISession.id == session_id).first()
        if db_session:
            db.delete(db_session)
            db.commit()

    return {"success": True, "message": "Session cancelled"}
