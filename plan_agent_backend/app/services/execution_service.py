from datetime import date, datetime
from typing import Optional

from sqlalchemy import func

from app.dependencies import SessionLocal
from app.models import Task, ExecutionLog


class ExecutionService:
    def log_daily_execution(
        self,
        user_id: int,
        log_date: date,
        difficulties: str | None = None,
        feedback: str | None = None,
    ) -> ExecutionLog:
        with SessionLocal() as db:
            tasks_completed = (
                db.query(func.count(Task.id))
                .filter(
                    Task.user_id == user_id,
                    Task.status == "completed",
                    func.date(Task.due_date) == log_date,
                )
                .scalar() or 0
            )

            tasks_total = (
                db.query(func.count(Task.id))
                .filter(
                    Task.user_id == user_id,
                    func.date(Task.due_date) == log_date,
                )
                .scalar() or 0
            )

            existing_log = (
                db.query(ExecutionLog)
                .filter(
                    ExecutionLog.user_id == user_id,
                    ExecutionLog.log_date == log_date,
                )
                .first()
            )

            if existing_log:
                existing_log.tasks_completed = tasks_completed
                existing_log.tasks_total = tasks_total
                if difficulties is not None:
                    existing_log.difficulties = difficulties
                if feedback is not None:
                    existing_log.feedback = feedback
                db.commit()
                db.refresh(existing_log)
                return existing_log

            new_log = ExecutionLog(
                user_id=user_id,
                log_date=log_date,
                tasks_completed=tasks_completed,
                tasks_total=tasks_total,
                difficulties=difficulties,
                feedback=feedback,
            )
            db.add(new_log)
            db.commit()
            db.refresh(new_log)
            return new_log

    def get_execution_logs(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[ExecutionLog]:
        with SessionLocal() as db:
            query = db.query(ExecutionLog).filter(ExecutionLog.user_id == user_id)

            if start_date:
                query = query.filter(ExecutionLog.log_date >= start_date)
            if end_date:
                query = query.filter(ExecutionLog.log_date <= end_date)

            return query.order_by(ExecutionLog.log_date.desc()).all()

    def get_execution_log(self, user_id: int, log_date: date) -> ExecutionLog | None:
        with SessionLocal() as db:
            return (
                db.query(ExecutionLog)
                .filter(
                    ExecutionLog.user_id == user_id,
                    ExecutionLog.log_date == log_date,
                )
                .first()
            )

    def update_execution_feedback(
        self,
        user_id: int,
        log_date: date,
        difficulties: str | None = None,
        feedback: str | None = None,
    ) -> ExecutionLog | None:
        with SessionLocal() as db:
            log = (
                db.query(ExecutionLog)
                .filter(
                    ExecutionLog.user_id == user_id,
                    ExecutionLog.log_date == log_date,
                )
                .first()
            )

            if not log:
                return self.log_daily_execution(
                    user_id=user_id,
                    log_date=log_date,
                    difficulties=difficulties,
                    feedback=feedback,
                )

            if difficulties is not None:
                log.difficulties = difficulties
            if feedback is not None:
                log.feedback = feedback

            db.commit()
            db.refresh(log)
            return log

    def get_execution_stats(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        with SessionLocal() as db:
            query = db.query(ExecutionLog).filter(ExecutionLog.user_id == user_id)

            if start_date:
                query = query.filter(ExecutionLog.log_date >= start_date)
            if end_date:
                query = query.filter(ExecutionLog.log_date <= end_date)

            logs = query.all()

            if not logs:
                return {
                    "total_days": 0,
                    "total_tasks": 0,
                    "total_completed": 0,
                    "average_completion_rate": 0,
                    "streak_days": 0,
                }

            total_tasks = sum(log.tasks_total for log in logs)
            total_completed = sum(log.tasks_completed for log in logs)
            average_rate = (total_completed / total_tasks * 100) if total_tasks > 0 else 0

            streak = 0
            today = date.today()
            for i in range(365):
                check_date = today - __import__('datetime').timedelta(days=i)
                log = next((l for l in logs if l.log_date == check_date), None)
                if log and log.tasks_completed > 0:
                    streak += 1
                elif i > 0:
                    break

            return {
                "total_days": len(logs),
                "total_tasks": total_tasks,
                "total_completed": total_completed,
                "average_completion_rate": round(average_rate, 2),
                "streak_days": streak,
            }


execution_service = ExecutionService()
