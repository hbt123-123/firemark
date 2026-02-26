import json
from enum import Enum
from datetime import datetime


from app.config import settings
from app.services.llm_service import llm_service
from app.utils.timezone import get_utc_now
from app.dependencies import SessionLocal
from app.models import AISession, Goal, Task


class DialogueState(str, Enum):
    AWAITING_OBJECTIVE = "awaiting_objective"
    AWAITING_REQUIREMENTS = "awaiting_requirements"
    AWAITING_RESOURCES = "awaiting_resources"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    COMPLETED = "completed"


class AIDialogueManager:
    STATE_QUESTIONS = {
        DialogueState.AWAITING_OBJECTIVE: {
            "questions": [
                {
                    "id": "objective_topic",
                    "question": "你想学习什么内容？请描述你的学习主题。",
                    "placeholder": "例如：Python编程、英语口语、数据分析...",
                },
                {
                    "id": "objective_criterion",
                    "question": "你希望达到什么样的水平？有什么具体的成功标准吗？",
                    "placeholder": "例如：能独立完成项目、通过某个考试、能进行日常对话...",
                },
                {
                    "id": "objective_motivation",
                    "question": "你学习这个的主要动力是什么？",
                    "placeholder": "例如：职业发展、个人兴趣、学业要求...",
                },
            ],
            "title": "🎯 学习目标",
            "description": "让我们先明确你的学习目标",
        },
        DialogueState.AWAITING_REQUIREMENTS: {
            "questions": [
                {
                    "id": "requirement_time",
                    "question": "你每周大概能投入多少时间学习？",
                    "placeholder": "例如：每周5小时、每天1小时...",
                },
                {
                    "id": "requirement_style",
                    "question": "你更喜欢什么样的学习方式？",
                    "placeholder": "例如：视频教程、阅读文档、动手实践、小组讨论...",
                },
                {
                    "id": "requirement_baseline",
                    "question": "你目前的基础水平如何？有相关经验吗？",
                    "placeholder": "例如：完全零基础、有一些基础、已经入门想提高...",
                },
            ],
            "title": "⏰ 学习要求",
            "description": "了解你的时间安排和学习偏好",
        },
        DialogueState.AWAITING_RESOURCES: {
            "questions": [
                {
                    "id": "resource_preference",
                    "question": "你有偏好的学习资源吗？或者希望我们推荐？",
                    "placeholder": "例如：有特定课程、希望推荐免费资源、偏好中文资源...",
                },
            ],
            "title": "📚 学习资源",
            "description": "确定你的学习资源偏好",
        },
        DialogueState.AWAITING_CONFIRMATION: {
            "questions": [],
            "title": "✅ 确认计划",
            "description": "请确认你的学习计划",
        },
    }

    STATE_TRANSITIONS = {
        DialogueState.AWAITING_OBJECTIVE: DialogueState.AWAITING_REQUIREMENTS,
        DialogueState.AWAITING_REQUIREMENTS: DialogueState.AWAITING_RESOURCES,
        DialogueState.AWAITING_RESOURCES: DialogueState.AWAITING_CONFIRMATION,
        DialogueState.AWAITING_CONFIRMATION: DialogueState.COMPLETED,
    }

    def __init__(self):
        from app.services.llm_service import llm_service
        self.llm_service = llm_service

    def get_initial_state(self) -> DialogueState:
        return DialogueState.AWAITING_OBJECTIVE

    def get_next_state(self, current_state: DialogueState) -> DialogueState:
        return self.STATE_TRANSITIONS.get(current_state, DialogueState.COMPLETED)

    def get_questions_for_state(self, state: DialogueState) -> dict:
        return self.STATE_QUESTIONS.get(state, {})

    async def process_answer(
        self, state: DialogueState, answer: str, session_data: dict
    ) -> dict:
        current_questions = self.get_questions_for_state(state)
        questions = current_questions.get("questions", [])

        if not questions:
            return session_data

        if "answers" not in session_data:
            session_data["answers"] = {}

        if "current_question_index" not in session_data:
            session_data["current_question_index"] = 0

        current_index = session_data["current_question_index"]

        if current_index < len(questions):
            question_id = questions[current_index]["id"]
            session_data["answers"][question_id] = answer
            session_data["current_question_index"] = current_index + 1

        if session_data["current_question_index"] >= len(questions):
            session_data["current_question_index"] = 0
            session_data["state"] = self.get_next_state(state).value

        return session_data

    def get_current_question(self, state: DialogueState, session_data: dict) -> dict | None:
        current_questions = self.get_questions_for_state(state)
        questions = current_questions.get("questions", [])

        if not questions:
            return None

        current_index = session_data.get("current_question_index", 0)

        if current_index < len(questions):
            return {
                **questions[current_index],
                "progress": {
                    "current": current_index + 1,
                    "total": len(questions),
                },
                "section_title": current_questions.get("title", ""),
                "section_description": current_questions.get("description", ""),
            }

        return None

    async def generate_plan_preview(self, session_data: dict) -> dict:
        answers = session_data.get("answers", {})

        prompt = f"""
Based on the following user input, generate a learning plan preview:

## User Answers:
{json.dumps(answers, ensure_ascii=False, indent=2)}

Please generate a JSON response with the following structure:
{{
    "goal": {{
        "title": "<goal title>",
        "description": "<goal description>",
        "start_date": "<YYYY-MM-DD>",
        "end_date": "<YYYY-MM-DD>",
        "objective_topic": "<topic>",
        "objective_criterion": "<criterion>",
        "objective_motivation": "<motivation>",
        "requirement_time": "<time requirement>",
        "requirement_style": "<style preference>",
        "requirement_baseline": "<baseline level>",
        "resource_preference": "<resource preference>"
    }},
    "outline": {{
        "total_phases": <number>,
        "phases": [
            {{
                "phase_number": <number>,
                "title": "<phase title>",
                "description": "<phase description>",
                "duration_weeks": <number>
            }}
        ]
    }},
    "preview_tasks": [
        {{
            "title": "<task title>",
            "description": "<task description>",
            "week": <week number>,
            "priority": <0/1/2>
        }}
    ],
    "summary": "<brief summary of the plan>"
}}
"""

        try:
            response = await llm_service.chat_raw(
                
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert learning plan designer. Generate structured plans in JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            return {
                "error": str(e),
                "goal": {"title": "学习计划", "description": "基于您的输入生成的学习计划"},
                "outline": {"total_phases": 1, "phases": []},
                "preview_tasks": [],
                "summary": "计划生成失败，请稍后重试",
            }

    def create_session(
        self, user_id: int, initial_input: str | None = None
    ) -> AISession:
        initial_state = self.get_initial_state()
        session_data = {
            "state": initial_state.value,
            "answers": {},
            "current_question_index": 0,
            "initial_input": initial_input,
        }

        session = AISession(
            user_id=user_id,
            state=initial_state.value,
            data=session_data,
        )

        with SessionLocal() as db:
            db.add(session)
            db.commit()
            db.refresh(session)

        return session

    def get_session(self, session_id: int, user_id: int) -> AISession | None:
        with SessionLocal() as db:
            return (
                db.query(AISession)
                .filter(AISession.id == session_id, AISession.user_id == user_id)
                .first()
            )

    def update_session(self, session: AISession, data: dict) -> AISession:
        with SessionLocal() as db:
            db_session = (
                db.query(AISession)
                .filter(AISession.id == session.id)
                .first()
            )
            if db_session:
                db_session.data = data
                db_session.state = data.get("state", db_session.state)
                db_session.updated_at = get_utc_now()
                db.commit()
                db.refresh(db_session)
                return db_session
        return session

    def create_goal_from_preview(
        self, user_id: int, preview: dict
    ) -> Goal:
        goal_data = preview.get("goal", {})

        goal = Goal(
            user_id=user_id,
            title=goal_data.get("title", "学习计划"),
            description=goal_data.get("description", ""),
            start_date=datetime.strptime(
                goal_data.get("start_date", datetime.now().strftime("%Y-%m-%d")),
                "%Y-%m-%d"
            ).date(),
            end_date=datetime.strptime(
                goal_data.get("end_date", (datetime.now() + __import__('datetime').timedelta(days=30)).strftime("%Y-%m-%d")),
                "%Y-%m-%d"
            ).date(),
            outline=preview.get("outline"),
            status="active",
            objective_topic=goal_data.get("objective_topic"),
            objective_criterion=goal_data.get("objective_criterion"),
            objective_motivation=goal_data.get("objective_motivation"),
            requirement_time=goal_data.get("requirement_time"),
            requirement_style=goal_data.get("requirement_style"),
            requirement_baseline=goal_data.get("requirement_baseline"),
            resource_preference=goal_data.get("resource_preference"),
        )

        with SessionLocal() as db:
            db.add(goal)
            db.commit()
            db.refresh(goal)

        return goal

    def create_tasks_from_preview(
        self, goal_id: int, user_id: int, preview_tasks: list
    ) -> list[Task]:
        tasks = []
        today = datetime.now().date()

        with SessionLocal() as db:
            for i, task_data in enumerate(preview_tasks):
                week = task_data.get("week", 1)
                due_date = today + __import__('datetime').timedelta(weeks=week)

                task = Task(
                    user_id=user_id,
                    goal_id=goal_id,
                    title=task_data.get("title", ""),
                    description=task_data.get("description", ""),
                    due_date=due_date,
                    status="pending",
                    priority=task_data.get("priority", 1),
                )
                db.add(task)
                tasks.append(task)

            db.commit()

        return tasks

    def complete_session(self, session_id: int) -> None:
        with SessionLocal() as db:
            session = db.query(AISession).filter(AISession.id == session_id).first()
            if session:
                session.state = DialogueState.COMPLETED.value
                session.updated_at = get_utc_now()
                db.commit()


ai_dialogue_manager = AIDialogueManager()
