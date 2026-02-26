from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from app.dependencies import get_current_user, SessionLocal
from app.models import User, FixedSchedule
from app.schemas import (
    FixedScheduleCreate,
    FixedScheduleUpdate,
    FixedScheduleResponse,
    FixedScheduleListResponse,
)


router = APIRouter(prefix="/fixed-schedules", tags=["fixed-schedules"])


@router.get("", response_model=FixedScheduleListResponse)
async def list_fixed_schedules(
    day_of_week: Optional[int] = Query(None, ge=0, le=6, description="Filter by day of week"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        query = db.query(FixedSchedule).filter(FixedSchedule.user_id == current_user.id)

        if day_of_week is not None:
            query = query.filter(FixedSchedule.day_of_week == day_of_week)
        if is_active is not None:
            query = query.filter(FixedSchedule.is_active == is_active)

        schedules = query.order_by(FixedSchedule.day_of_week, FixedSchedule.start_time).all()

        return FixedScheduleListResponse(
            schedules=schedules,
            total=len(schedules),
        )


@router.get("/{schedule_id}", response_model=FixedScheduleResponse)
async def get_fixed_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        schedule = (
            db.query(FixedSchedule)
            .filter(
                FixedSchedule.id == schedule_id,
                FixedSchedule.user_id == current_user.id,
            )
            .first()
        )

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fixed schedule not found",
            )

        return schedule


@router.post("", response_model=FixedScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_fixed_schedule(
    schedule_data: FixedScheduleCreate,
    current_user: User = Depends(get_current_user),
):
    if schedule_data.start_time >= schedule_data.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time must be before end time",
        )

    with SessionLocal() as db:
        new_schedule = FixedSchedule(
            user_id=current_user.id,
            title=schedule_data.title,
            description=schedule_data.description,
            day_of_week=schedule_data.day_of_week,
            start_time=schedule_data.start_time,
            end_time=schedule_data.end_time,
            repeat_rule=schedule_data.repeat_rule,
            is_active=schedule_data.is_active,
        )
        db.add(new_schedule)
        db.commit()
        db.refresh(new_schedule)

        return new_schedule


@router.put("/{schedule_id}", response_model=FixedScheduleResponse)
async def update_fixed_schedule(
    schedule_id: int,
    schedule_data: FixedScheduleUpdate,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        schedule = (
            db.query(FixedSchedule)
            .filter(
                FixedSchedule.id == schedule_id,
                FixedSchedule.user_id == current_user.id,
            )
            .first()
        )

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fixed schedule not found",
            )

        update_data = schedule_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(schedule, field, value)

        start_time = schedule.start_time
        end_time = schedule.end_time
        if start_time >= end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time must be before end time",
            )

        db.commit()
        db.refresh(schedule)

        return schedule


@router.delete("/{schedule_id}")
async def delete_fixed_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        schedule = (
            db.query(FixedSchedule)
            .filter(
                FixedSchedule.id == schedule_id,
                FixedSchedule.user_id == current_user.id,
            )
            .first()
        )

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fixed schedule not found",
            )

        db.delete(schedule)
        db.commit()

        return {"success": True, "message": "Fixed schedule deleted"}


@router.post("/{schedule_id}/activate")
async def activate_fixed_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        schedule = (
            db.query(FixedSchedule)
            .filter(
                FixedSchedule.id == schedule_id,
                FixedSchedule.user_id == current_user.id,
            )
            .first()
        )

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fixed schedule not found",
            )

        schedule.is_active = True
        db.commit()

        return {"success": True, "message": "Fixed schedule activated"}


@router.post("/{schedule_id}/deactivate")
async def deactivate_fixed_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        schedule = (
            db.query(FixedSchedule)
            .filter(
                FixedSchedule.id == schedule_id,
                FixedSchedule.user_id == current_user.id,
            )
            .first()
        )

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fixed schedule not found",
            )

        schedule.is_active = False
        db.commit()

        return {"success": True, "message": "Fixed schedule deactivated"}


@router.get("/day/{day_of_week}", response_model=FixedScheduleListResponse)
async def get_schedules_by_day(
    day_of_week: int,
    current_user: User = Depends(get_current_user),
):
    if day_of_week < 0 or day_of_week > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="day_of_week must be between 0 (Monday) and 6 (Sunday)",
        )

    with SessionLocal() as db:
        schedules = (
            db.query(FixedSchedule)
            .filter(
                FixedSchedule.user_id == current_user.id,
                FixedSchedule.day_of_week == day_of_week,
                FixedSchedule.is_active == True,
            )
            .order_by(FixedSchedule.start_time)
            .all()
        )

        return FixedScheduleListResponse(
            schedules=schedules,
            total=len(schedules),
        )
