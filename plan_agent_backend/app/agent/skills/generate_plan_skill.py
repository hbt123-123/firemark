"""
Generate Plan Skill - 生成学习计划

迁移自 app/skills/generate_plan_skill.py
"""
import json
from datetime import date, timedelta

from app.agent.skills.base import BaseSkill
from app.agent.types import SkillResult
from app.dependencies import SessionLocal
from app.models import User, Goal, Task, UserMemory, FixedSchedule
from app.services.llm_service import llm_service
from app.utils.timezone import get_utc_now


class GeneratePlanSkill(BaseSkill):
    name = "generate_plan"
    description = "Generate a learning plan with outline and initial tasks based on user's goal and requirements."
    input_schema = {
        "type": "object",
        "properties": {
            "goal_id": {
                "type": "integer",
                "description": "The goal ID to generate plan for",
            },
            "additional_context": {
                "type": "string",
                "description": "Additional context or requirements from user",
            },
        },
        "required": ["goal_id"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "outline": {
                "type": "object",
                "description": "Generated plan outline with milestones",
            },
            "tasks": {
                "type": "array",
                "description": "Generated initial tasks",
            },
            "recommendations": {
                "type": "array",
                "description": "Recommendations for the user",
            },
        },
    }

    def __init__(self):
        pass  # 使用全局 llm_service

    async def _get_user_context(self, user_id: int) -> dict:
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            
            memories = (
                db.query(UserMemory)
                .filter(UserMemory.user_id == user_id)
                .order_by(UserMemory.created_at.desc())
                .limit(10)
                .all()
            )
            
            fixed_schedules = (
                db.query(FixedSchedule)
                .filter(FixedSchedule.user_id == user_id, FixedSchedule.is_active == True)  # noqa: E712
                .all()
            )
            
            return {
                "preferences": user.preferences or {},
                "memories": [
                    {"type": m.memory_type, "content": m.content}
                    for m in memories
                ],
                "fixed_schedules": [
                    {
                        "title": s.title,
                        "day_of_week": s.day_of_week,
                        "start_time": s.start_time,
                        "end_time": s.end_time,
                    }
                    for s in fixed_schedules
                ],
            }

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
                "objective_topic": goal.objective_topic,
                "objective_criterion": goal.objective_criterion,
                "objective_motivation": goal.objective_motivation,
                "requirement_time": goal.requirement_time,
                "requirement_style": goal.requirement_style,
                "requirement_baseline": goal.requirement_baseline,
                "resource_preference": goal.resource_preference,
            }

    async def _call_llm(self, prompt: str) -> dict:
        try:
            response = await llm_service.chat_raw(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert learning plan designer. Generate structured, actionable plans in JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except json.JSONDecodeError as e:
            from app.exceptions import ErrorCode
            # 返回错误信息而不是静默吞掉
            return {
                "error": ErrorCode.ERR_LLM_002.value,
                "error_message": "AI 响应格式错误",
                "details": str(e)
            }
        except Exception as e:
            from app.exceptions import ErrorCode
            return {
                "error": ErrorCode.ERR_LLM_001.value,
                "error_message": ErrorCode.ERR_LLM_001.message,
                "details": str(e)
            }

    async def _save_tasks(self, goal_id: int, user_id: int, tasks: list) -> list:
        created_tasks = []
        with SessionLocal() as db:
            for task_data in tasks:
                due_date = task_data.get("due_date")
                if isinstance(due_date, str):
                    due_date = date.fromisoformat(due_date)
                else:
                    due_date = date.today() + timedelta(days=task_data.get("days_from_now", 1))
                
                task = Task(
                    user_id=user_id,
                    goal_id=goal_id,
                    title=task_data.get("title", ""),
                    description=task_data.get("description", ""),
                    due_date=due_date,
                    due_time=task_data.get("due_time"),
                    status="pending",
                    priority=task_data.get("priority", 1),
                    dependencies=task_data.get("dependencies"),
                )
                db.add(task)
                created_tasks.append(task_data)
            
            db.commit()
        
        return created_tasks

    async def _update_goal_outline(self, goal_id: int, outline: dict) -> None:
        with SessionLocal() as db:
            goal = db.query(Goal).filter(Goal.id == goal_id).first()
            if goal:
                goal.outline = outline
                db.commit()

    async def execute(self, parameters: dict, user_id: int | None = None) -> SkillResult:
        goal_id = parameters.get("goal_id")
        additional_context = parameters.get("additional_context", "")
        
        if not goal_id or not user_id:
            return SkillResult(success=False, error="goal_id and user_id are required")
        
        goal_info = await self._get_goal_info(goal_id, user_id)
        if not goal_info:
            return SkillResult(success=False, error="Goal not found or access denied")
        
        user_context = await self._get_user_context(user_id)
        
        prompt = f"""
Based on the following information, generate a comprehensive learning plan:

## Goal Information:
{json.dumps(goal_info, ensure_ascii=False, indent=2)}

## User Context:
- Preferences: {json.dumps(user_context.get('preferences', {}), ensure_ascii=False)}
- Learning History: {json.dumps(user_context.get('memories', []), ensure_ascii=False)}
- Fixed Schedules: {json.dumps(user_context.get('fixed_schedules', []), ensure_ascii=False)}

## Additional Context:
{additional_context}

Please generate a JSON response with the following structure:
{{
    "outline": {{
        "total_phases": <number>,
        "phases": [
            {{
                "phase_number": <number>,
                "title": "<phase title>",
                "description": "<phase description>",
                "duration_weeks": <number>,
                "milestones": ["<milestone1>", "<milestone2>"]
            }}
        ],
        "estimated_total_hours": <number>
    }},
    "tasks": [
        {{
            "title": "<task title>",
            "description": "<task description>",
            "days_from_now": <number>,
            "due_time": "<HH:MM or null>",
            "priority": <0/1/2>,
            "phase": <phase number>
        }}
    ],
    "recommendations": [
        "<recommendation1>",
        "<recommendation2>"
    ]
}}
"""
        
        llm_result = await self._call_llm(prompt)
        
        if "error" in llm_result:
            return SkillResult(success=False, error=f"LLM error: {llm_result['error']}")
        
        outline = llm_result.get("outline", {})
        tasks = llm_result.get("tasks", [])
        recommendations = llm_result.get("recommendations", [])
        
        await self._update_goal_outline(goal_id, outline)
        
        saved_tasks = await self._save_tasks(goal_id, user_id, tasks)
        
        return SkillResult(
            success=True,
            data={
                "outline": outline,
                "tasks": saved_tasks,
                "recommendations": recommendations,
            },
            metadata={
                "goal_id": goal_id,
                "generated_at": get_utc_now().isoformat(),
            },
        )


# 自动注册
from app.agent.registry import plugin_registry
plugin_registry.register_skill(GeneratePlanSkill())
