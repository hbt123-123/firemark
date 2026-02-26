"""
Web Search Tool - 网络搜索工具

迁移自 app/tools/web_search_tool.py
"""
from typing import Any
import httpx

from app.config import settings
from app.agent.tools.base import BaseTool
from app.agent.types import ToolResult


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web using SerpAPI and return relevant results."
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string",
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return (default: 5)",
                "default": 5,
            },
        },
        "required": ["query"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "results": {
                "type": "array",
                "description": "List of search results",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "link": {"type": "string"},
 {"type": "                        "snippet":string"},
                    },
                },
            },
            "total_results": {"type": "integer"},
        },
    }

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.SERP_API_KEY
        self.base_url = "https://serpapi.com/search"

    async def execute(self, parameters: dict, user_id: int | None = None) -> ToolResult:
        query = parameters.get("query", "").strip()
        num_results = parameters.get("num_results", 5)
        
        if not query:
            return ToolResult(success=False, error="Search query is required")
        
        if not self.api_key:
            return ToolResult(
                success=False,
                error="SerpAPI key is not configured. Please set SERP_API_KEY in environment.",
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "q": query,
                        "api_key": self.api_key,
                        "num": num_results,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
            
            results = []
            organic_results = data.get("organic_results", [])
            
            for item in organic_results[:num_results]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                })
            
            return ToolResult(
                success=True,
                data={
                    "results": results,
                    "total_results": len(results),
                    "query": query,
                },
            )
        except httpx.HTTPStatusError as e:
            return ToolResult(
                success=False,
                error=f"Search API error: {e.response.status_code}",
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Search failed: {str(e)}")


# 自动注册
from app.agent.registry import plugin_registry
plugin_registry.register_tool(WebSearchTool())
