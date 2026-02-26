import logging
import random
from datetime import date
from typing import Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.dependencies import SessionLocal
from app.models import UserWordSettings, WordBank, DailyWordTask

logger = logging.getLogger(__name__)


# 默认值常量
DEFAULT_DAILY_COUNT = 10
DEFAULT_REPEAT_EN = 2
DEFAULT_REPEAT_ZH = 1
DEFAULT_ENABLE_NOTIFICATION = True


def generate_daily_words(
    db: Session,
    user_id: int,
    target_date: date,
) -> Optional[DailyWordTask]:
    """
    生成每日单词任务

    Args:
        db: 数据库会话（需从外部传入）
        user_id: 用户ID
        target_date: 目标日期

    Returns:
        DailyWordTask对象，如果用户设置不存在则返回None

    工作流程:
        1. 查询用户设置，若不存在则返回None
        2. 根据selected_tags筛选单词（任一标签匹配）
        3. 若筛选结果少于daily_count，取全部
        4. 随机打乱并取前daily_count个
        5. 创建DailyWordTask记录
        6. 若当天已存在任务，直接返回已存在的任务
    """
    # 1. 查询用户设置
    settings = (
        db.query(UserWordSettings).filter(UserWordSettings.user_id == user_id).first()
    )

    if settings is None:
        return None

    # 2. 检查当天是否已存在任务（get_or_create模式）
    existing_task = (
        db.query(DailyWordTask)
        .filter(
            and_(
                DailyWordTask.user_id == user_id,
                DailyWordTask.task_date == target_date,
            )
        )
        .first()
    )

    if existing_task:
        return existing_task

    # 获取用户设置
    daily_count = settings.daily_count or DEFAULT_DAILY_COUNT
    selected_tags = settings.selected_tags

    # 3. 筛选单词
    if selected_tags and len(selected_tags) > 0:
        # PostgreSQL ARRAY字段：筛选包含任一标签的单词
        # 使用 any() 方法
        words_query = db.query(WordBank.id).filter(WordBank.tags.any(selected_tags))
    else:
        # 如果没有选择标签，获取所有单词
        words_query = db.query(WordBank.id)

    # 执行查询获取所有匹配的单词ID
    all_word_ids = [row[0] for row in words_query.all()]

    # 4. 处理单词数量不足的情况
    if len(all_word_ids) == 0:
        # 没有匹配的单词，返回None或创建空任务
        # 没有匹配的单词，返回None或创建空任务
        return None

    # 如果单词数量不足daily_count，取全部
    actual_count = min(daily_count, len(all_word_ids))

    # 5. 随机打乱并选取
    random.shuffle(all_word_ids)
    selected_word_ids = all_word_ids[:actual_count]

    # 6. 创建每日单词任务
    new_task = DailyWordTask(
        user_id=user_id,
        task_date=target_date,
        word_ids=selected_word_ids,
        completed_count=0,
        status="pending",
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


def get_user_settings(db: Session, user_id: int) -> Optional[UserWordSettings]:
    """
    获取用户单词设置

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        UserWordSettings对象，若不存在则返回None
    """
    return (
        db.query(UserWordSettings).filter(UserWordSettings.user_id == user_id).first()
    )


def update_user_settings(
    db: Session,
    user_id: int,
    selected_tags: Optional[list[str]] = None,
    daily_count: Optional[int] = None,
    repeat_en: Optional[int] = None,
    repeat_zh: Optional[int] = None,
    enable_notification: Optional[bool] = None,
) -> UserWordSettings:
    """
    更新用户单词设置

    Args:
        db: 数据库会话
        user_id: 用户ID
        selected_tags: 选择的标签
        daily_count: 每日学习数量
        repeat_en: 英文重复次数
        repeat_zh: 中文重复次数
        enable_notification: 是否启用通知

    Returns:
        更新后的UserWordSettings对象
    """
    settings = (
        db.query(UserWordSettings).filter(UserWordSettings.user_id == user_id).first()
    )

    if settings is None:
        # 创建新设置
        settings = UserWordSettings(
            user_id=user_id,
            selected_tags=selected_tags,
            daily_count=daily_count or DEFAULT_DAILY_COUNT,
            repeat_en=repeat_en or DEFAULT_REPEAT_EN,
            repeat_zh=repeat_zh or DEFAULT_REPEAT_ZH,
            enable_notification=enable_notification
            if enable_notification is not None
            else DEFAULT_ENABLE_NOTIFICATION,
        )
        db.add(settings)
    else:
        # 更新现有设置
        if selected_tags is not None:
            settings.selected_tags = selected_tags
        if daily_count is not None:
            settings.daily_count = daily_count
        if repeat_en is not None:
            settings.repeat_en = repeat_en
        if repeat_zh is not None:
            settings.repeat_zh = repeat_zh
        if enable_notification is not None:
            settings.enable_notification = enable_notification

    db.commit()
    db.refresh(settings)
    return settings


def get_daily_task(
    db: Session,
    user_id: int,
    target_date: date,
) -> Optional[DailyWordTask]:
    """
    获取指定日期的每日单词任务

    Args:
        db: 数据库会话
        user_id: 用户ID
        target_date: 目标日期

    Returns:
        DailyWordTask对象，若不存在则返回None
    """
    return (
        db.query(DailyWordTask)
        .filter(
            and_(
                DailyWordTask.user_id == user_id,
                DailyWordTask.task_date == target_date,
            )
        )
        .first()
    )


def update_task_progress(
    db: Session,
    task_id: int,
    completed_count: int,
) -> Optional[DailyWordTask]:
    """
    更新任务进度

    Args:
        db: 数据库会话
        task_id: 任务ID
        completed_count: 已完成数量

    Returns:
        更新后的DailyWordTask对象
    """
    task = db.query(DailyWordTask).filter(DailyWordTask.id == task_id).first()

    if task is None:
        return None

    task.completed_count = completed_count

    # 如果已完成数量等于总单词数，更新状态
    if completed_count >= len(task.word_ids):
        task.status = "completed"
    db.commit()
    db.refresh(task)
    return task


def get_or_create_daily_words(
    db: Session,
    user_id: int,
    target_date: date,
) -> Optional[DailyWordTask]:
    """
    获取或创建每日单词任务

    该函数复用generate_daily_words的逻辑，用于get_or_create模式。

    Args:
        db: 数据库会话
        user_id: 用户ID
        target_date: 目标日期

    Returns:
        DailyWordTask对象，如果用户设置不存在则返回None
    """
    return generate_daily_words(db, user_id, target_date)


def get_words_by_ids(db: Session, word_ids: list[int]) -> list[WordBank]:
    """
    根据ID列表查询单词详情

    Args:
        db: 数据库会话
        word_ids: 单词ID列表

    Returns:
        WordBank对象列表（按传入ID顺序）
    """
    if not word_ids:
        return []

    # 查询单词并保持ID顺序
    words = (
        db.query(WordBank)
        .filter(WordBank.id.in_(word_ids))
        .all()
    )

    # 按word_ids顺序排序
    word_dict = {word.id: word for word in words}
    return [word_dict[wid] for wid in word_ids if wid in word_dict]


def generate_all_daily_tasks(target_date: date) -> dict:
    """
    为所有用户生成每日单词任务

    Args:
        target_date: 目标日期

    Returns:
        dict: 包含成功和失败数量的字典
    """
    success_count = 0
    fail_count = 0
    skipped_count = 0

    logger.info(f"Starting generate_all_daily_tasks for {target_date}")

    try:
        with SessionLocal() as db:
            # 查询所有有设置的用户ID
            users = db.query(UserWordSettings).all()
            user_ids = [u.user_id for u in users]

        logger.info(f"Found {len(user_ids)} users with word settings")

        # 在with块外部处理每个用户，每个用户使用独立的session
        for user_id in user_ids:
            try:
                with SessionLocal() as db_inner:
                    # 生成每日任务（如果当天不存在）
                    task = generate_daily_words(db_inner, user_id, target_date)
                    if task is None:
                        skipped_count += 1
                        logger.debug(f"User {user_id}: No settings or no words available")
                    else:
                        success_count += 1
                        logger.debug(f"User {user_id}: Generated task with {len(task.word_ids)} words")
            except Exception as e:
                fail_count += 1
                logger.error(f"Error generating daily words for user {user_id}: {e}")

    except Exception as e:
        logger.error(f"Error in generate_all_daily_tasks: {e}")

    result = {
        "success": success_count,
        "failed": fail_count,
        "skipped": skipped_count,
        "total": success_count + fail_count + skipped_count,
    }

    logger.info(f"generate_all_daily_tasks completed: {result}")
    return result
