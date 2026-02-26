"""
Send Notification Tool - 发送通知工具

迁移自 app/tools/send_notification_tool.py
"""
from typing import Any
import httpx

from app.config import settings
from app.agent.tools.base import BaseTool
from app.agent.types import ToolResult


class SendNotificationTool(BaseTool):
    name = "send_notification"
    description = "Send push notification to a user via JPush (极光推送)."
    input_schema = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Notification title",
            },
            "content": {
                "type": "string",
                "description": "Notification content/body",
            },
            "push_token": {
                "type": "string",
                "description": "Target device push token (optional, uses user's token if not provided)",
            },
            "extras": {
                "type": "object",
                "description": "Additional data to include in the notification",
            },
        },
        "required": ["title", "content"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message_id": {"type": "string"},
            "sendno": {"type": "string"},
        },
    }

    def __init__(
        self,
        app_key: str | None = None,
        master_secret: str | None = None,
    ):
        self.app_key = app_key or settings.JPUSH_APP_KEY
        self.master_secret = master_secret or settings.JPUSH_MASTER_SECRET
        self.base_url = "https://api.jpush.cn/v3/push"

    async def execute(self, parameters: dict, user_id: int | None = None) -> ToolResult:
        title = parameters.get("title", "").strip()
        content = parameters.get("content", "").strip()
        push_token = parameters.get("push_token")
        extras = parameters.get("extras", {})
        
        if not title or not content:
            return ToolResult(success=False, error="Title and content are required")
        
        if not self.app_key or not self.master_secret:
            return ToolResult(
                success=False,
                error="JPush credentials are not configured. Please set JPUSH_APP_KEY and JPUSH_MASTER_SECRET.",
            )
        
        if not push_token and not user_id:
            return ToolResult(
                success=False,
                error="Either push_token or user_id must be provided",
            )
        
        if not push_token and user_id:
            from app.dependencies import SessionLocal
            from app.models import User
            
            with SessionLocal() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.push_token:
                    return ToolResult(
                        success=False,
                        error="User not found or has no push token registered",
                    )
                push_token = user.push_token
        
        payload = {
            "platform": "all",
            "audience": {
                "registration_id": [push_token]
            },
            "notification": {
                "android": {
                    "alert": content,
                    "title": title,
                    "extras": extras,
                },
                "ios": {
                    "alert": {
                        "title": title,
                        "body": content,
                    },
                    "extras": extras,
                },
            },
            "options": {
                "time_to_live": 86400,
                "apns_production": not settings.DEBUG,
            },
        }
        
        try:
            import base64
            credentials = base64.b64encode(
                f"{self.app_key}:{self.master_secret}".encode()
            ).decode()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers={
                        "Authorization": f"Basic {credentials}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
            
            return ToolResult(
                success=True,
                data={
                    "message_id": data.get("msg_id"),
                    "sendno": data.get("sendno"),
                    "status": "sent",
                },
            )
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = e.response.text
            return ToolResult(
                success=False,
                error=f"JPush API error: {e.response.status_code} - {error_detail}",
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Notification failed: {str(e)}")


# 自动注册
from app.agent.registry import plugin_registry
plugin_registry.register_tool(SendNotificationTool())
