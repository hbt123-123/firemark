"""
Adjust Tasks Skill - 调整任务

迁移自 app/skills/adjust_tasks_skill.py
"""
import json
from datetime import date, timedelta

from app.agent.skills.base import BaseSkill
from app.agent.types import SkillResult
from app.dependencies import SessionLocal
from app.models import Goal, Task, ExecutionLog, ReflectionLog
from app.services.llm_service import llm_service
from app.utils.timezone import get_utc_now


class AdjustTasksSkill(BaseSkill):
    name = "adjust_tasks"
    description = "Analyze execution logs and adjust task plan based on user feedback and progress."
    input_schema = {
        "type": "object",
        "properties": {
            "goal_id": {
                "type": "integer",
                "description": "The goal ID to adjust tasks for",
            },
            "feedback": {
                "type": "string",
                "description": "User feedback on current progress",
            },
            "adjustment_type": {
                "type": "string",
                "enum": ["reschedule", "rebalance", "simplify", "intensify"],
                "description": "Type of adjustment to make",
            },
        },
        "required": ["goal_id"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "adjustments": {
                "type": "array",
                "description": "List of adjustments made",
            },
            "analysis": {
                "type": "string",
                "description": "LLM analysis of the situation",
            },
            "reflection_log_id": {
                "type": "integer",
                "description": "ID of created reflection log",
            },
        },
    }

    def __init__(self):
        pass  # 使用全局 llm_service

    async def _get_goal_tasks(self, goal_id: int, user_id: int) -> list[dict]:
        with SessionLocal() as db:
            tasks = (
                db.query(Task)
                .filter(Task.goal_id == goal_id, Task.user_id == user_id)
                .order_by(Task.due_date)
                .all()
            )
            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "due_date": t.due_date.isoformat(),
                    "due_time": t.due_time,
                    "status": t.status,
                    "priority": t.priority,
                    "dependencies": t.dependencies,
                }
                for t in tasks
            ]

    async def _get_execution_logs(self, user_id: int, days: int = 7) -> list[dict]:
        with SessionLocal() as db:
            start_date = date.today() - timedelta(days=days)
            logs = (
                db.query(ExecutionLog)
                .filter(
                    ExecutionLog.user_id == user_id,
                    ExecutionLog.log_date >= start_date,
                )
                .order_by(ExecutionLog.log_date.desc())
                .all()
            )
            return [
                {
                    "log_date": l.log_date.isoformat(),
                    "tasks_completed": l.tasks_completed,
                    "tasks_total": l.tasks_total,
                    "difficulties": l.difficulties,
                    "feedback": l.feedback,
                }
                for l in logs
            ]

    async def _get_goal_info(self, goal_id: int, user_id: int) -> dict | None:
        with SessionLocal() as db:
            goal = (
                db.query(Goal)
                .filter(Goal.id == goal_id, Goal.user_id == user_id)
                .first()
            )
            if not goal:
                return None
            
            return {
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "start_date": goal.start_date.isoformat(),
                "end_date": goal.end_date.isoformat(),
                "status": goal.status,
                "current_phase": goal.current_phase,
                "outline": goal.outline,
            }

    async def _call_llm(self, prompt: str) -> dict:
        try:
            response = await llm_service.chat_raw(
                
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert learning plan adjuster. Analyze progress and suggest adjustments in JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            return {"error": str(e)}

    async def _apply_adjustments(self, goal_id: int, user_id: int, adjustments: list) -> list:
        applied = []
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
                    if adj.get("new_due_time"):
                        task.due_time = adj.get("new_due_time")
                    applied.append({"task_id": task_id, "action": action, "status": "applied"})
                
                elif action == "change_priority":
                    task.priority = adj.get("new_priority", task.priority)
                    applied.append({"task_id": task_id, "action": action, "status": "applied"})
                
                elif action == "mark_completed":
                    task.status = "completed"
                    applied.append({"task_id": task_id, "action": action, "status": "applied"})
                
                elif action == "mark_skipped":
                    task.status = "skipped"
                    applied.append({"task_id": task_id, "action": action, "status": "applied"})
                
                elif action == "add_task":
                    new_task = Task(
                        user_id=user_id,
                        goal_id=goal_id,
                        title=adj.get("title", ""),
                        description=adj.get("description", ""),
                        due_date=date.fromisoformat(adj.get("due_date", date.today().isoformat())),
                        due_time=adj.get("due_time"),
                        status="pending",
                        priority=adj.get("priority", 1),
                    )
                    db.add(new_task)
                    applied.append({"action": "add_task", "title": adj.get("title"), "status": "created"})
                
                elif action == "remove_task":
                    task.status = "skipped"
                    applied.append({"task_id": task_id, "action": "remove_task", "status": "skipped"})
            
            db.commit()
        
        return applied

    async def _create_reflection_log(
        self, user_id: int, goal_id: int, analysis: str, adjustment_plan: dict
    ) -> int:
        with SessionLocal() as db:
            log = ReflectionLog(
                user_id=user_id,
                goal_id=goal_id,
                reflection_time=get_utc_now(),
                analysis=analysis,
                adjustment_plan=adjustment_plan,
                applied=True,
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            return log.id

    async def execute(self, parameters: dict, user_id: int | None = None) -> SkillResult:
        goal_id = parameters.get("goal_id")
        feedback = parameters.get("feedback", "")
        adjustment_type = parameters.get("adjustment_type", "reschedule")
        
        if not goal_id or not user_id:
            return SkillResult(success=False, error="goal_id and user_id are required")
        
        goal_info = await self._get_goal_info(goal_id, user_id)
        if not goal_info:
            return SkillResult(success=False, error="Goal not found or access denied")
        
        tasks = await self._get_goal_tasks(goal_id, user_id)
        execution_logs = await self._get_execution_logs(user_id)
        
        prompt = f"""
Analyze the following learning plan and execution data, then suggest adjustments:

## Goal Information:
{json.dumps(goal_info, ensure_ascii=False, indent=2)}

## Current Tasks:
{json.dumps(tasks, ensure_ascii=False, indent=2)}

## Recent Execution Logs:
{json.dumps(execution_logs, ensure_ascii=False, indent=2)}

## User Feedback:
{feedback}

## Adjustment Type Requested: {adjustment_type}

Please generate a JSON response with the following structure:
{{
    "analysis": "<detailed analysis of the situation>",
    "adjustments": [
        {{
            "task_id": <task id or null for new tasks>,
            "action": "<reschedule|change_priority|mark_completed|mark_skipped|add_task|remove_task>",
            "new_due_date": "<YYYY-MM-DD or null>",
            "new_due_time": "<HH:MM or null>",
            "new_priority": <0/1/2 or null>,
            "title": "<for add_task>",
            "description": "<for add_task>",
            "reason": "<why this adjustment>"
        }}
    ],
    "recommendations": ["<recommendation1>", "<recommendation2>"]
}}
"""
        
        llm_result = await self._call_llm(prompt)
        
        if "error" in llm_result:
            return SkillResult(success=False, error=f"LLM error: {llm_result['error']}")
        
        analysis = llm_result.get("analysis", "")
        adjustments = llm_result.get("adjustments", [])
        recommendations = llm_result.get("recommendations", [])
        
        applied_adjustments = await self._apply_adjustments(goal_id, user_id, adjustments)
        
        reflection_log_id = await self._create_reflection_log(
            user_id, goal_id, analysis, {"adjustments": adjustments, "recommendations": recommendations}
        )
        
        return SkillResult(
            success=True,
            data={
                "adjustments": applied_adjustments,
                "analysis": analysis,
                "recommendations": recommendations,
                "reflection_log_id": reflection_log_id,
            },
            metadata={
                "goal_id": goal_id,
                "adjustment_type": adjustment_type,
                "adjusted_at": get_utc_now().isoformat(),
            },
        )


# 自动注册
from app.agent.registry import plugin_registry
plugin_registry.register_skill(AdjustTasksSkill())
