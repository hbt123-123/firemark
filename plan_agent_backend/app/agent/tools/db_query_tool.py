"""
DB Query Tool - 数据库查询工具

迁移自 app/tools/db_query_tool.py
"""
import re
from typing import Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.agent.tools.base import BaseTool
from app.agent.types import ToolResult
from app.dependencies import SessionLocal


ALLOWED_TABLES = {
    "users": ["id", "username", "created_at"],
    "goals": ["id", "user_id", "title", "description", "status", "start_date", "end_date"],
    "tasks": ["id", "user_id", "goal_id", "title", "description", "due_date", "status", "priority"],
    "fixed_schedules": ["id", "user_id", "title", "day_of_week", "start_time", "end_time"],
    "execution_logs": ["id", "user_id", "log_date", "tasks_completed", "tasks_total"],
    "reflection_logs": ["id", "user_id", "goal_id", "reflection_time", "applied"],
}

FORBIDDEN_PATTERNS = [
    r"\bDELETE\b",
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bCREATE\b",
    r"\bTRUNCATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r";.*",
    r"--",
    r"/\*",
]


class DBQueryTool(BaseTool):
    name = "db_query"
    description = "Execute read-only SQL queries on allowed tables. Only SELECT statements are permitted."
    input_schema = {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": "The SQL SELECT query to execute",
            }
        },
        "required": ["sql"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "rows": {"type": "array", "description": "Query results"},
            "row_count": {"type": "integer", "description": "Number of rows returned"},
        },
    }

    def _validate_sql(self, sql: str) -> tuple[bool, str]:
        sql_upper = sql.upper().strip()
        
        if not sql_upper.startswith("SELECT"):
            return False, "Only SELECT statements are allowed"
        
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                return False, f"Forbidden SQL pattern detected"
        
        table_match = re.search(r"\bFROM\s+(\w+)", sql, re.IGNORECASE)
        if table_match:
            table_name = table_match.group(1).lower()
            if table_name not in ALLOWED_TABLES:
                return False, f"Table '{table_name}' is not allowed for querying"
        
        return True, ""

    def _inject_user_filter(self, sql: str, user_id: int) -> str:
        where_match = re.search(r"\bWHERE\b", sql, re.IGNORECASE)
        
        table_match = re.search(r"\bFROM\s+(\w+)", sql, re.IGNORECASE)
        if not table_match:
            return sql
        
        table_name = table_match.group(1).lower()
        if table_name not in ALLOWED_TABLES:
            return sql
        
        user_filter = f"user_id = {user_id}"
        
        if where_match:
            sql = re.sub(
                r"\bWHERE\b",
                f"WHERE {user_filter} AND",
                sql,
                count=1,
                flags=re.IGNORECASE,
            )
        else:
            sql = re.sub(
                r"\bFROM\s+(\w+)",
                f"FROM \\1 WHERE {user_filter}",
                sql,
                count=1,
                flags=re.IGNORECASE,
            )
        
        return sql

    async def execute(self, parameters: dict, user_id: int | None = None) -> ToolResult:
        sql = parameters.get("sql", "").strip()
        
        if not sql:
            return ToolResult(success=False, error="SQL query is required")
        
        is_valid, error_msg = self._validate_sql(sql)
        if not is_valid:
            return ToolResult(success=False, error=error_msg)
        
        if user_id:
            sql = self._inject_user_filter(sql, user_id)
        
        try:
            with SessionLocal() as db:
                result = db.execute(text(sql))
                columns = result.keys() if result.returns_rows else []
                rows = [dict(zip(columns, row)) for row in result.fetchall()] if result.returns_rows else []
                
                return ToolResult(
                    success=True,
                    data={
                        "rows": rows,
                        "row_count": len(rows),
                        "columns": list(columns),
                    },
                )
        except Exception as e:
            return ToolResult(success=False, error=f"Query execution failed: {str(e)}")


# 自动注册
from app.agent.registry import plugin_registry
plugin_registry.register_tool(DBQueryTool())
