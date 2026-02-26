import json
from datetime import date, timedelta

from app.dependencies import SessionLocal
from app.models import User, Goal, Task, ExecutionLog, ReflectionLog
from app.agent.skills.adjust_tasks_skill import AdjustTasksSkill
from app.services.llm_service import llm_service
from app.utils.timezone import get_utc_now


class ReflectionService:
    def __init__(self):
        self.adjust_skill = AdjustTasksSkill()

    async def get_execution_logs_for_reflection(
        self,
        user_id: int,
        days: int = 7,
        goal_id: int | None = None,
    ) -> list[dict]:
        with SessionLocal() as db:
            start_date = date.today() - timedelta(days=days)
            query = db.query(ExecutionLog).filter(
                ExecutionLog.user_id == user_id,
                ExecutionLog.log_date >= start_date,
            )

            logs = query.order_by(ExecutionLog.log_date.desc()).all()

            return [
                {
                    "log_date": l.log_date.isoformat(),
                    "tasks_completed": l.tasks_completed,
                    "tasks_total": l.tasks_total,
                    "completion_rate": (
                        l.tasks_completed / l.tasks_total * 100
                        if l.tasks_total > 0
                        else 0
                    ),
                    "difficulties": l.difficulties,
                    "feedback": l.feedback,
                }
                for l in logs
            ]

    async def get_tasks_for_reflection(
        self,
        user_id: int,
        goal_id: int | None = None,
    ) -> list[dict]:
        with SessionLocal() as db:
            query = db.query(Task).filter(Task.user_id == user_id)

            if goal_id:
                query = query.filter(Task.goal_id == goal_id)

            tasks = query.order_by(Task.due_date).limit(50).all()

            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "due_date": t.due_date.isoformat(),
                    "due_time": t.due_time,
                    "status": t.status,
                    "priority": t.priority,
                    "goal_id": t.goal_id,
                }
                for t in tasks
            ]

    async def get_goal_outline(self, goal_id: int) -> dict | None:
        with SessionLocal() as db:
            goal = db.query(Goal).filter(Goal.id == goal_id).first()
            if goal:
                return {
                    "id": goal.id,
                    "title": goal.title,
                    "description": goal.description,
                    "status": goal.status,
                    "current_phase": goal.current_phase,
                    "outline": goal.outline,
                }
            return None

    async def call_reflection_llm(
        self,
        execution_logs: list[dict],
        tasks: list[dict],
        goal_outline: dict | None = None,
    ) -> dict:
        prompt = f"""
You are an expert learning plan reflection assistant. Analyze the following data and provide structured recommendations.

## Recent Execution Logs (Last 7 Days):
{json.dumps(execution_logs, ensure_ascii=False, indent=2)}

## Current Tasks:
{json.dumps(tasks, ensure_ascii=False, indent=2)}

## Goal Outline:
{json.dumps(goal_outline, ensure_ascii=False, indent=2) if goal_outline else "No specific goal context"}

Please analyze the data and provide recommendations in the following JSON format:
{{
    "analysis": {{
        "overall_progress": "<brief analysis of overall progress>",
        "completion_trend": "<analysis of completion trend>",
        "key_issues": ["<issue1>", "<issue2>"],
        "positive_aspects": ["<aspect1>", "<aspect2>"]
    }},
    "recommendations": {{
        "task_adjustments": [
            {{
                "task_id": <id>,
                "action": "<reschedule|change_priority|mark_completed|mark_skipped>",
                "new_due_date": "<YYYY-MM-DD or null>",
                "new_priority": <0/1/2 or null>,
                "reason": "<why this adjustment>"
            }}
        ],
        "new_tasks": [
            {{
                "title": "<task title>",
                "description": "<description>",
                "due_date": "<YYYY-MM-DD>",
                "priority": <0/1/2>,
                "reason": "<why add this task>"
            }}
        ],
        "general_suggestions": ["<suggestion1>", "<suggestion2>"]
    }},
    "reflection_summary": "<brief summary of the reflection>"
}}
"""

        try:
            result = await llm_service.chat_with_json(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert learning plan reflection assistant. Provide structured, actionable recommendations in JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            return result
        except Exception as e:
            return {
                "error": str(e),
                "analysis": {
                    "overall_progress": "Unable to analyze",
                    "completion_trend": "Unknown",
                    "key_issues": [],
                    "positive_aspects": [],
                },
                "recommendations": {
                    "task_adjustments": [],
                    "new_tasks": [],
                    "general_suggestions": [],
                },
                "reflection_summary": f"Reflection failed: {str(e)}",
            }

    async def save_reflection_log(
        self,
        user_id: int,
        goal_id: int | None,
        analysis: str,
        adjustment_plan: dict,
        applied: bool = False,
    ) -> ReflectionLog:
        with SessionLocal() as db:
            log = ReflectionLog(
                user_id=user_id,
                goal_id=goal_id,
                reflection_time=get_utc_now(),
                analysis=analysis,
                adjustment_plan=adjustment_plan,
                applied=applied,
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            return log

    async def apply_adjustments(
        self,
        user_id: int,
        goal_id: int | None,
        recommendations: dict,
    ) -> dict:
        adjustments = recommendations.get("task_adjustments", [])
        new_tasks = recommendations.get("new_tasks", [])

        applied_count = 0
        created_count = 0

        with SessionLocal() as db:
            for adj in adjustments:
                task_id = adj.get("task_id")
                action = adj.get("action")

                if not task_id or not action:
                    continue

                task = (
                    db.query(Task)
                    .filter(Task.id == task_id, Task.user_id == user_id)
                    .first()
                )

                if not task:
                    continue

                if action == "reschedule":
                    new_date = adj.get("new_due_date")
                    if new_date:
                        task.due_date = date.fromisoformat(new_date)
                    applied_count += 1

                elif action == "change_priority":
                    task.priority = adj.get("new_priority", task.priority)
                    applied_count += 1

                elif action == "mark_completed":
                    task.status = "completed"
                    applied_count += 1

                elif action == "mark_skipped":
                    task.status = "skipped"
                    applied_count += 1

            if goal_id:
                for task_data in new_tasks:
                    new_task = Task(
                        user_id=user_id,
                        goal_id=goal_id,
                        title=task_data.get("title", ""),
                        description=task_data.get("description", ""),
                        due_date=date.fromisoformat(
                            task_data.get("due_date", date.today().isoformat())
                        ),
                        status="pending",
                        priority=task_data.get("priority", 1),
                    )
                    db.add(new_task)
                    created_count += 1

            db.commit()

        return {
            "adjusted_tasks": applied_count,
            "created_tasks": created_count,
        }

    async def run_reflection(
        self,
        user_id: int,
        goal_id: int | None = None,
        auto_apply: bool = True,
    ) -> dict:
        execution_logs = await self.get_execution_logs_for_reflection(
            user_id=user_id, days=7, goal_id=goal_id
        )

        tasks = await self.get_tasks_for_reflection(user_id=user_id, goal_id=goal_id)

        goal_outline = None
        if goal_id:
            goal_outline = await self.get_goal_outline(goal_id)

        llm_result = await self.call_reflection_llm(
            execution_logs=execution_logs,
            tasks=tasks,
            goal_outline=goal_outline,
        )

        if "error" in llm_result and "analysis" not in llm_result.get("analysis", {}):
            return {
                "success": False,
                "error": llm_result.get("error"),
            }

        analysis = json.dumps(llm_result.get("analysis", {}), ensure_ascii=False)
        recommendations = llm_result.get("recommendations", {})
        summary = llm_result.get("reflection_summary", "")

        applied = False
        apply_result = None

        if auto_apply:
            apply_result = await self.apply_adjustments(
                user_id=user_id,
                goal_id=goal_id,
                recommendations=recommendations,
            )
            applied = True

        reflection_log = await self.save_reflection_log(
            user_id=user_id,
            goal_id=goal_id,
            analysis=analysis,
            adjustment_plan={
                "recommendations": recommendations,
                "summary": summary,
            },
            applied=applied,
        )

        return {
            "success": True,
            "reflection_log_id": reflection_log.id,
            "analysis": llm_result.get("analysis", {}),
            "recommendations": recommendations,
            "summary": summary,
            "applied": applied,
            "apply_result": apply_result,
        }

    def get_reflection_logs(
        self,
        user_id: int,
        goal_id: int | None = None,
        limit: int = 10,
    ) -> list[ReflectionLog]:
        with SessionLocal() as db:
            query = db.query(ReflectionLog).filter(ReflectionLog.user_id == user_id)

            if goal_id:
                query = query.filter(ReflectionLog.goal_id == goal_id)

            return query.order_by(ReflectionLog.created_at.desc()).limit(limit).all()


reflection_service = ReflectionService()
