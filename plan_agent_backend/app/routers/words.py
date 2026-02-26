from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import DailyWordTask, User, UserWordSettings
from app.schemas import (
    DailyStat,
    DailyWordsResponse,
    WordCompleteRequest,
    WordCompleteResponse,
    WordDetail,
    WordSettingsResponse,
    WordSettingsUpdate,
    WordStatsResponse,
)
from app.services.word_service import (
    get_or_create_daily_words,
    get_words_by_ids,
)

router = APIRouter(prefix="/words", tags=["words"])


DEFAULT_DAILY_COUNT = 10
DEFAULT_REPEAT_EN = 2
DEFAULT_REPEAT_ZH = 1
DEFAULT_ENABLE_NOTIFICATION = True


@router.get("/settings", response_model=WordSettingsResponse)
async def get_word_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的单词设置"""
    settings = (
        db.query(UserWordSettings)
        .filter(UserWordSettings.user_id == current_user.id)
        .first()
    )

    if settings is None:
        return WordSettingsResponse(
            id=0,
            user_id=current_user.id,
            selected_tags=[],
            daily_count=DEFAULT_DAILY_COUNT,
            repeat_en=DEFAULT_REPEAT_EN,
            repeat_zh=DEFAULT_REPEAT_ZH,
            enable_notification=DEFAULT_ENABLE_NOTIFICATION,
            updated_at=datetime.utcnow(),
        )

    return settings


@router.post("/settings", response_model=WordSettingsResponse)
async def update_word_settings(
    settings_data: WordSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存或更新用户单词设置"""
    update_values = settings_data.model_dump(exclude_unset=True)
    if not update_values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided",
        )

    settings = (
        db.query(UserWordSettings)
        .filter(UserWordSettings.user_id == current_user.id)
        .first()
    )

    if settings is None:
        new_settings = UserWordSettings(
            user_id=current_user.id,
            selected_tags=update_values.get("selected_tags", []),
            daily_count=update_values.get("daily_count", DEFAULT_DAILY_COUNT),
            repeat_en=update_values.get("repeat_en", DEFAULT_REPEAT_EN),
            repeat_zh=update_values.get("repeat_zh", DEFAULT_REPEAT_ZH),
            enable_notification=update_values.get(
                "enable_notification", DEFAULT_ENABLE_NOTIFICATION
            ),
        )
        db.add(new_settings)
        db.commit()
        db.refresh(new_settings)
        return new_settings

    for field, value in update_values.items():
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)
    return settings


@router.get("/daily", response_model=DailyWordsResponse)
async def get_daily_words(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    date: date = Query(default=None, description="日期，格式YYYY-MM-DD，默认当天"),
):
    """获取每日单词任务"""
    target_date = date if date else date.today()

    settings = (
        db.query(UserWordSettings)
        .filter(UserWordSettings.user_id == current_user.id)
        .first()
    )

    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未设置单词偏好，请先设置",
        )

    task = get_or_create_daily_words(db, current_user.id, target_date)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="无法生成每日单词任务",
        )

    words = get_words_by_ids(db, task.word_ids)

    word_details = [
        WordDetail(
            id=w.id,
            word=w.word,
            translation=w.translation,
            phonetic_us=w.pronunciation,
            phonetic_uk=w.pronunciation,
            part_of_speech=w.part_of_speech,
            audio_url_en=w.audio_url_en,
            audio_url_zh=w.audio_url_zh,
            examples=w.examples,
        )
        for w in words
    ]

    return DailyWordsResponse(
        task_id=task.id,
        task_date=task.task_date,
        total_count=len(task.word_ids),
        completed_count=task.completed_count,
        status=task.status,
        words=word_details,
    )


@router.post("/daily/complete", response_model=WordCompleteResponse)
async def complete_word(
    request: WordCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记单词完成"""
    target_date = request.date if request.date else date.today()

    task = (
        db.query(DailyWordTask)
        .filter(
            and_(
                DailyWordTask.user_id == current_user.id,
                DailyWordTask.task_date == target_date,
            )
        )
        .first()
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="当天任务不存在",
        )

    if request.word_id not in task.word_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的单词ID，该单词不在今日任务中",
        )

    total_count = len(task.word_ids)
    current_completed = task.completed_count

    if current_completed >= total_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="今日任务已完成",
        )

    new_completed = current_completed + 1
    task.completed_count = new_completed

    if new_completed >= total_count:
        task.status = "completed"

    db.commit()
    db.refresh(task)

    return WordCompleteResponse(
        completed=new_completed,
        total=total_count,
        status=task.status,
    )


@router.get("/stats", response_model=WordStatsResponse)
async def get_word_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_date: date = Query(
        default=None,
        description="开始日期，格式YYYY-MM-DD，默认30天前",
    ),
    end_date: date = Query(
        default=None,
        description="结束日期，格式YYYY-MM-DD，默认当天",
    ),
):
    """
    获取单词学习统计

    - 查询指定日期范围内的学习记录
    - 返回总天数、分配单词数、完成数、完成率、日均完成数
    """
    # 设置默认日期
    today = date.today()
    if end_date is None:
        end_date = today
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    # 查询日期范围内的任务
    tasks = (
        db.query(DailyWordTask)
        .filter(
            DailyWordTask.user_id == current_user.id,
            DailyWordTask.task_date >= start_date,
            DailyWordTask.task_date <= end_date,
        )
        .all()
    )

    if not tasks:
        return WordStatsResponse(
            total_days=0,
            total_words_assigned=0,
            total_words_completed=0,
            completion_rate=0.0,
            daily_average=0.0,
            daily_details=[],
        )

    # 计算统计
    total_days = len(tasks)
    total_words_assigned = sum(len(task.word_ids) for task in tasks)
    total_words_completed = sum(task.completed_count for task in tasks)

    # 计算完成率
    completion_rate = (
        total_words_completed / total_words_assigned
        if total_words_assigned > 0
        else 0.0
    )

    # 计算日均完成数
    daily_average = total_words_completed / total_days if total_days > 0 else 0.0

    # 每日详情
    daily_details = [
        DailyStat(
            date=task.task_date,
            total_words=len(task.word_ids),
            completed_words=task.completed_count,
            status=task.status,
        )
        for task in tasks
    ]

    return WordStatsResponse(
        total_days=total_days,
        total_words_assigned=total_words_assigned,
        total_words_completed=total_words_completed,
        completion_rate=round(completion_rate, 2),
        daily_average=round(daily_average, 2),
        daily_details=daily_details,
    )
