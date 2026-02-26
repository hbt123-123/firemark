"""
Agent 核心 - LLM 调用封装
"""
import json


from app.agent.registry import plugin_registry
from app.services.llm_service import llm_service


class LLMClient:
    """LLM 客户端封装 - 使用统一的 LLMService"""
    
    def __init__(self):
        self._service = llm_service
    
    @property
    def client(self):
        return self._service.client
    
    @property
    def model(self):
        return self._service.model
    
    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
    ) -> dict:
        """发送聊天请求"""
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if tools:
            params["tools"] = tools
            if tool_choice:
                params["tool_choice"] = tool_choice
        
        response = await self.client.chat.completions.create(**params)
        return response.choices[0].message.model_dump()
    
    async def chat_with_json(
        self,
        messages: list[dict],
        temperature: float = 0.7,
    ) -> dict:
        """发送聊天请求，要求返回 JSON"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return json.loads(content)


class IntentRecognizer:
    """意图识别器"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    async def recognize(self, message: str, context: dict | None = None) -> dict:
        """
        识别用户意图
        
        Returns:
            {
                "intent": "create_plan",
                "confidence": 0.95,
                "entities": {"topic": "Python"}
            }
        """
        system_prompt = """你是一个意图识别助手。根据用户的消息，识别其意图。

可能的意图类型：
- create_plan: 用户想要创建学习计划
- adjust_plan: 用户想要调整学习计划
- ask_question: 用户在提问
- update_task: 用户想要更新任务状态
- view_progress: 用户想要查看进度
- clarification: 用户在澄清或纠正
- chat: 普通聊天

请返回JSON格式：
{
    "intent": "意图类型",
    "confidence": 0.95,
    "entities": {"提取的实体信息"}
}"""
        
        user_prompt = f"用户消息：{message}"
        if context:
            user_prompt += f"\n上下文：{json.dumps(context, ensure_ascii=False)}"
        
        try:
            result = await self.llm.chat_with_json([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ], temperature=0.3)
            return result
        except Exception as e:
            return {
                "intent": "chat",
                "confidence": 0.5,
                "entities": {},
                "error": str(e)
            }


class ToolExecutor:
    """工具执行器"""
    
    def __init__(self):
        self.registry = plugin_registry
    
    async def execute(self, tool_calls: list[dict], user_id: int | None = None) -> list[dict]:
        """批量执行工具调用"""
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("function", {}).get("name")
            arguments_str = tool_call.get("function", {}).get("arguments", "{}")
            
            try:
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError:
                arguments = {}
            
            tool = self.registry.get_tool(tool_name)
            if not tool:
                results.append({
                    "tool_call_id": tool_call.get("id"),
                    "content": f"Error: Tool '{tool_name}' not found",
                    "is_error": True,
                })
                continue
            
            try:
                result = await tool.execute(arguments, user_id)
                results.append({
                    "tool_call_id": tool_call.get("id"),
                    "content": json.dumps(result.data) if result.success else result.error,
                    "is_error": not result.success,
                })
            except Exception as e:
                results.append({
                    "tool_call_id": tool_call.get("id"),
                    "content": f"Error: {str(e)}",
                    "is_error": True,
                })
        
        return results


class SkillExecutor:
    """Skill 执行器"""
    
    def __init__(self):
        self.registry = plugin_registry
    
    async def execute(
        self, 
        skill_name: str, 
        parameters: dict, 
        user_id: int | None = None
    ) -> dict:
        """执行 Skill"""
        skill = self.registry.get_skill(skill_name)
        if not skill:
            return {"success": False, "error": f"Skill '{skill_name}' not found"}
        
        try:
            result = await skill.execute(parameters, user_id)
            return result.model_dump()
        except Exception as e:
            return {"success": False, "error": str(e)}


# 全局实例
llm_client = LLMClient()
intent_recognizer = IntentRecognizer(llm_client)
tool_executor = ToolExecutor()
skill_executor = SkillExecutor()
