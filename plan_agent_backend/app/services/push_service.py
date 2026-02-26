import json
from datetime import datetime, date, timedelta
from typing import Any


from app.services.llm_service import llm_service
from app.dependencies import SessionLocal
from app.models import User, Task, ExecutionLog
from app.agent.tools.send_notification_tool import SendNotificationTool


class PushService:
    def __init__(self):
        self.llm_service = llm_service
        self.notification_tool = SendNotificationTool()

    async def get_upcoming_tasks(self, minutes: int = 30) -> list[dict]:
        now = datetime.now()
        end_time = now + timedelta(minutes=minutes)

        with SessionLocal() as db:
            today = date.today()
            current_time = now.strftime("%H:%M")

            tasks = (
                db.query(Task)
                .filter(
                    Task.status == "pending",
                    Task.due_date == today,
                    Task.due_time >= current_time,
                    Task.due_time <= end_time.strftime("%H:%M"),
                )
                .all()
            )

            result = []
            for task in tasks:
                user = db.query(User).filter(User.id == task.user_id).first()
                if user and user.push_token:
                    result.append({
                        "task_id": task.id,
                        "user_id": task.user_id,
                        "username": user.username,
                        "push_token": user.push_token,
                        "title": task.title,
                        "due_time": task.due_time,
                    })

            return result

    async def send_task_reminder(self, task_info: dict) -> dict:
        try:
            result = await self.notification_tool.execute(
                parameters={
                    "title": "任务提醒",
                    "content": f"您的任务「{task_info['title']}」将在{task_info['due_time']}开始，请做好准备！",
                    "push_token": task_info["push_token"],
                    "extras": {
                        "type": "task_reminder",
                        "task_id": task_info["task_id"],
                    },
                },
                user_id=task_info["user_id"],
            )

            return {
                "success": result.success,
                "task_id": task_info["task_id"],
                "user_id": task_info["user_id"],
                "error": result.error if not result.success else None,
            }
        except Exception as e:
            return {
                "success": False,
                "task_id": task_info["task_id"],
                "user_id": task_info["user_id"],
                "error": str(e),
            }

    async def send_task_reminders(self) -> dict:
        tasks = await self.get_upcoming_tasks(minutes=30)

        results = []
        for task_info in tasks:
            result = await self.send_task_reminder(task_info)
            results.append(result)

        success_count = sum(1 for r in results if r["success"])

        return {
            "total_tasks": len(tasks),
            "sent_successfully": success_count,
            "failed": len(tasks) - success_count,
            "details": results,
        }

    async def get_user_daily_summary(self, user_id: int) -> dict:
        today = date.today()

        with SessionLocal() as db:
            tasks = (
                db.query(Task)
                .filter(
                    Task.user_id == user_id,
                    Task.due_date == today,
                )
                .all()
            )

            completed = [t for t in tasks if t.status == "completed"]
            pending = [t for t in tasks if t.status == "pending"]
            skipped = [t for t in tasks if t.status == "skipped"]

            execution_log = (
                db.query(ExecutionLog)
                .filter(
                    ExecutionLog.user_id == user_id,
                    ExecutionLog.log_date == today,
                )
                .first()
            )

            return {
                "total_tasks": len(tasks),
                "completed_count": len(completed),
                "pending_count": len(pending),
                "skipped_count": len(skipped),
                "completion_rate": (len(completed) / len(tasks) * 100) if tasks else 0,
                "completed_titles": [t.title for t in completed],
                "pending_titles": [t.title for t in pending],
                "difficulties": execution_log.difficulties if execution_log else None,
                "feedback": execution_log.feedback if execution_log else None,
            }

    async def generate_review_message(self, user_id: int, summary: dict) -> str:
        prompt = f"""
Based on the following daily task summary, generate a personalized evening review message for the user.
Be encouraging and provide helpful suggestions. Keep the message concise (under 200 characters).

## Daily Summary:
- Total tasks: {summary['total_tasks']}
- Completed: {summary['completed_count']}
- Pending: {summary['pending_count']}
- Completion rate: {summary['completion_rate']:.1f}%
- Completed tasks: {', '.join(summary['completed_titles']) if summary['completed_titles'] else 'None'}
- Pending tasks: {', '.join(summary['pending_titles']) if summary['pending_titles'] else 'None'}
- Difficulties: {summary.get('difficulties', 'None')}
- Feedback: {summary.get('feedback', 'None')}

Generate a short, personalized message in Chinese that:
1. Acknowledges their progress
2. Provides encouragement
3. Gives a brief suggestion for tomorrow

Output only the message text, no JSON or formatting.
"""

        try:
            response = await self.llm_client.chat.completions.create(
                model=settings.LLM_MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful study companion that provides encouraging evening review messages.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                max_tokens=200,
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            if summary["completed_count"] > 0:
                return f"今天完成了{summary['completed_count']}个任务，继续保持！明天会更好！"
            else:
                return "今天辛苦了！明天继续加油，相信你可以做得更好！"

    async def send_evening_review_for_user(self, user: User) -> dict:
        if not user.push_token:
            return {
                "success": False,
                "user_id": user.id,
                "error": "No push token registered",
            }

        try:
            summary = await self.get_user_daily_summary(user.id)

            if summary["total_tasks"] == 0:
                return {
                    "success": False,
                    "user_id": user.id,
                    "error": "No tasks today",
                }

            review_message = await self.generate_review_message(user.id, summary)

            result = await self.notification_tool.execute(
                parameters={
                    "title": "今日复盘",
                    "content": review_message,
                    "push_token": user.push_token,
                    "extras": {
                        "type": "evening_review",
                        "summary": summary,
                    },
                },
                user_id=user.id,
            )

            return {
                "success": result.success,
                "user_id": user.id,
                "message": review_message,
                "error": result.error if not result.success else None,
            }
        except Exception as e:
            return {
                "success": False,
                "user_id": user.id,
                "error": str(e),
            }

    async def send_evening_review(self) -> dict:
        with SessionLocal() as db:
            users = db.query(User).filter(User.push_token.isnot(None)).all()

        results = []
        for user in users:
            result = await self.send_evening_review_for_user(user)
            results.append(result)

        success_count = sum(1 for r in results if r["success"])

        return {
            "total_users": len(users),
            "sent_successfully": success_count,
            "failed": len(users) - success_count,
            "details": results,
        }


push_service = PushService()
