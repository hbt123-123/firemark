import logging
from datetime import datetime, date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.dependencies import SessionLocal
from app.models import User, Goal
from app.services.reflection_service import reflection_service
from app.services.execution_service import execution_service
from app.services.push_service import push_service
from app.services.word_service import generate_all_daily_tasks
from app.utils.timezone import get_utc_now

logger = logging.getLogger(__name__)


scheduler = AsyncIOScheduler()


async def run_daily_reflection_for_user(user_id: int):
    try:
        with SessionLocal() as db:
            active_goals = (
                db.query(Goal)
                .filter(Goal.user_id == user_id, Goal.status == "active")
                .all()
            )

        for goal in active_goals:
            try:
                await reflection_service.run_reflection(
                    user_id=user_id,
                    goal_id=goal.id,
                    auto_apply=True,
                )
            except Exception as e:
                logger.info(
                    f"Error running reflection for user {user_id}, goal {goal.id}: {e}"
                )

        if not active_goals:
            try:
                await reflection_service.run_reflection(
                    user_id=user_id,
                    goal_id=None,
                    auto_apply=True,
                )
            except Exception as e:
                logger.info(f"Error running general reflection for user {user_id}: {e}")

    except Exception as e:
        logger.info(f"Error in daily reflection for user {user_id}: {e}")


async def daily_reflection_job():
    logger.info(f"Starting daily reflection job at {get_utc_now()}")

    try:
        with SessionLocal() as db:
            users = db.query(User).all()

        for user in users:
            await run_daily_reflection_for_user(user.id)

        logger.info(f"Daily reflection job completed for {len(users)} users")
    except Exception as e:
        logger.info(f"Error in daily reflection job: {e}")


async def daily_execution_log_job():
    logger.info(f"Starting daily execution log job at {get_utc_now()}")

    try:
        today = datetime.now().date()

        with SessionLocal() as db:
            users = db.query(User).all()

        for user in users:
            try:
                execution_service.log_daily_execution(
                    user_id=user.id,
                    log_date=today,
                )
            except Exception as e:
                logger.info(f"Error generating execution log for user {user.id}: {e}")

        logger.info(f"Daily execution log job completed for {len(users)} users")
    except Exception as e:
        logger.info(f"Error in daily execution log job: {e}")


async def task_reminder_job():
    logger.info(f"Starting task reminder job at {get_utc_now()}")

    try:
        result = await push_service.send_task_reminders()
        logger.info(
            f"Task reminder job completed: {result['sent_successfully']}/{result['total_tasks']} sent"
        )
    except Exception as e:
        logger.info(f"Error in task reminder job: {e}")


async def evening_review_job():
    logger.info(f"Starting evening review job at {get_utc_now()}")

    try:
        result = await push_service.send_evening_review()
        logger.info(
            f"Evening review job completed: {result['sent_successfully']}/{result['total_users']} sent"
        )
    except Exception as e:
        logger.info(f"Error in evening review job: {e}")


async def daily_word_task_job():
    """每日单词任务定时任务"""
    logger.info(f"Starting daily word task job at {get_utc_now()}")

    try:
        # 生成明天的任务（凌晨执行时）
        target_date = date.today() + timedelta(days=1)
        result = generate_all_daily_tasks(target_date)
        logger.info(f"Daily word task job completed: {result}")
    except Exception as e:
        logger.error(f"Error in daily word task job: {e}")


def setup_scheduler():
    scheduler.add_job(
        daily_reflection_job,
        CronTrigger(hour=2, minute=0),
        id="daily_reflection",
        name="Daily Reflection Job",
        replace_existing=True,
    )

    scheduler.add_job(
        daily_execution_log_job,
        CronTrigger(hour=23, minute=55),
        id="daily_execution_log",
        name="Daily Execution Log Job",
        replace_existing=True,
    )

    scheduler.add_job(
        task_reminder_job,
        IntervalTrigger(minutes=30),
        id="task_reminder",
        name="Task Reminder Job",
        replace_existing=True,
    )

    scheduler.add_job(
        evening_review_job,
        CronTrigger(hour=21, minute=0),
        id="evening_review",
        name="Evening Review Job",
        replace_existing=True,
    )

    # 每日单词任务 - 每天凌晨0:05执行，生成明天的任务
    scheduler.add_job(
        daily_word_task_job,
        CronTrigger(hour=0, minute=5),
        id="daily_word_task",
        name="Daily Word Task Job",
        replace_existing=True,
    )

    print("Scheduler setup completed. Jobs scheduled:")
    print("  - Daily Reflection: 02:00 UTC")
    print("  - Daily Execution Log: 23:55 UTC")
    print("  - Task Reminder: Every 30 minutes")
    print("  - Evening Review: 21:00 UTC")
    print("  - Daily Word Task: 00:05 UTC (generates next day's tasks)")


def start_scheduler():
    if not scheduler.running:
        setup_scheduler()
        scheduler.start()
        print("Scheduler started")


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler shutdown")
