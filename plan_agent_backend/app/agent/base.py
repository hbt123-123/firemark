"""
Agent - 核心智能体类
"""
import json
import uuid
from typing import Any, Optional

from app.agent.core import llm_client, intent_recognizer, tool_executor, skill_executor
from app.agent.memory import short_term_memory, long_term_memory
from app.agent.registry import plugin_registry
from app.agent.types import Decision, Intent


class Agent:
    """
    智能体核心类
    
    提供 LLM-driven 的智能对话能力，支持：
    - 意图识别
    - 工具调用
    - Skill 执行
    - 记忆管理
    """
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.llm = llm_client
        self.intent_recognizer = intent_recognizer
        self.tool_executor = tool_executor
        self.skill_executor = skill_executor
        self.short_memory = short_term_memory
        self.long_memory = long_term_memory
        self.registry = plugin_registry
    
    async def chat(
        self,
        user_id: int,
        message: str,
        session_id: str | None = None,
    ) -> dict:
        """
        处理用户消息
        
        Args:
            user_id: 用户 ID
            message: 用户消息
            session_id: 会话 ID（可选）
        
        Returns:
            {
                "response": "AI 回复",
                "session_id": "会话 ID",
                "intent": "识别到的意图",
                "tool_calls": [...],  # 如果有工具调用
            }
        """
        # 创建或获取会话
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        ctx = self.short_memory.get_session(session_id)
        if not ctx:
            ctx = self.short_memory.create_session(session_id, user_id)
        
        # 添加用户消息
        self.short_memory.add_message(session_id, "user", message)
        
        # 获取上下文
        messages = self.short_memory.get_context_for_llm(session_id)
        messages.append({"role": "user", "content": message})
        
        # 获取长期记忆
        user_profile = self.long_memory.get_user_profile(user_id)
        
        # 识别意图
        intent_result = await self.intent_recognizer.recognize(
            message, 
            context={"user_profile": user_profile, "state": ctx.state}
        )
        
        intent = intent_result.get("intent", "chat")
        entities = intent_result.get("entities", {})
        
        # 根据意图处理
        if intent in ["create_plan", "adjust_plan", "ask_question", "view_progress"]:
            response = await self._handle_goal_intent(
                session_id, user_id, message, intent, entities
            )
        elif intent == "update_task":
            response = await self._handle_task_update(session_id, user_id, message, entities)
        elif intent == "clarification":
            response = await self._handle_clarification(session_id, message)
        else:
            # 普通聊天
            response = await self._handle_chat(session_id, user_id, message)
        
        # 添加 AI 消息
        self.short_memory.add_message(session_id, "assistant", response)
        
        return {
            "response": response,
            "session_id": session_id,
            "intent": intent,
            "entities": entities,
        }
    
    async def _handle_goal_intent(
        self,
        session_id: str,
        user_id: int,
        message: str,
        intent: str,
        entities: dict,
    ) -> str:
        """处理目标相关的意图"""
        # 检查是否需要收集更多信息
        ctx = self.short_memory.get_session(session_id)
        if not ctx:
            return "会话已过期，请重新开始。"
        
        # 检查收集的信息是否足够
        required_fields = ["topic", "goal_title"]
        missing = [f for f in required_fields if f not in ctx.collected_info]
        
        if missing and intent == "create_plan":
            # 收集信息
            if "topic" in entities:
                self.short_memory.collect_info(session_id, "topic", entities["topic"])
            if "goal_title" in entities:
                self.short_memory.collect_info(session_id, "goal_title", entities["goal_title"])
            
            # 检查还缺什么
            missing = [f for f in required_fields if f not in ctx.collected_info]
            if missing:
                questions = {
                    "topic": "你想学习什么内容？请告诉我你的学习目标。",
                    "goal_title": "请为你的学习计划起一个名字。",
                }
                question = questions.get(missing[0], "请告诉我更多信息。")
                return question
        
        # 信息足够，执行对应的 Skill
        if intent == "create_plan":
            # 调用 generate_plan skill
            goal_id = ctx.collected_info.get("goal_id")
            if not goal_id:
                # 需要先创建 Goal
                return "要创建学习计划，我需要先了解一下你的目标。请告诉我你想学习什么？"
            
            result = await self.skill_executor.execute(
                "generate_plan",
                {"goal_id": goal_id},
                user_id
            )
            
            if result.get("success"):
                plan = result.get("data", {})
                return f"学习计划已生成！\n\n{json.dumps(plan, ensure_ascii=False, indent=2)}"
            else:
                return f"生成计划时出错：{result.get('error')}"
        
        return "我理解你的意图了。让我继续帮你处理。"
    
    async def _handle_task_update(
        self,
        session_id: str,
        user_id: int,
        message: str,
        entities: dict,
    ) -> str:
        """处理任务更新"""
        ctx = self.short_memory.get_session(session_id)
        
        # 调用 adjust_tasks skill
        result = await self.skill_executor.execute(
            "adjust_tasks",
            {
                "goal_id": entities.get("goal_id"),
                "feedback": message,
                "adjustment_type": "rebalance",
            },
            user_id
        )
        
        if result.get("success"):
            return "任务已更新！"
        else:
            return f"更新任务时出错：{result.get('error')}"
    
    async def _handle_clarification(
        self,
        session_id: str,
        message: str,
    ) -> str:
        """处理澄清"""
        ctx = self.short_memory.get_session(session_id)
        
        # 清除之前的收集信息，重新开始
        self.short_memory.update_state(session_id, "collecting_info")
        
        return "明白了，让我们重新开始。请告诉我你的学习目标是什么？"
    
    async def _handle_chat(
        self,
        session_id: str,
        user_id: int,
        message: str,
    ) -> str:
        """处理普通聊天"""
        messages = self.short_memory.get_context_for_llm(session_id)
        messages.append({"role": "user", "content": message})
        
        try:
            result = await self.llm.chat(messages, temperature=0.7)
            return result.get("content", "抱歉，我无法理解你的意思。")
        except Exception as e:
            return f"处理消息时出错：{str(e)}"
    
    async def execute_skill(
        self,
        skill_name: str,
        parameters: dict,
        user_id: int,
    ) -> dict:
        """直接执行 Skill"""
        return await self.skill_executor.execute(skill_name, parameters, user_id)
    
    def get_tools(self) -> list[dict]:
        """获取可用工具列表"""
        return self.registry.list_tools()
    
    def get_skills(self) -> list[dict]:
        """获取可用技能列表"""
        return self.registry.list_skills()


# 全局默认 Agent
default_agent = Agent("default")
