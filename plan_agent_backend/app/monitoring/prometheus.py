"""
Prometheus 指标监控中间件
"""

import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse


# ============================================================
# 定义指标
# ============================================================

# HTTP 请求计数器
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

# HTTP 请求持续时间直方图
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# 活跃请求数
http_requests_active = Gauge("http_requests_active", "Number of active HTTP requests")

# API 请求计数器（按用户）
api_requests_by_user = Counter(
    "api_requests_by_user", "API requests by user", ["user_id", "endpoint"]
)

# 业务指标
tasks_created_total = Counter("tasks_created_total", "Total tasks created")

tasks_completed_total = Counter("tasks_completed_total", "Total tasks completed")

goals_created_total = Counter("goals_created_total", "Total goals created")

# AI 代理指标
ai_requests_total = Counter(
    "ai_requests_total",
    "Total AI requests",
    ["intent", "status"],
)

ai_request_duration_seconds = Histogram(
    "ai_request_duration_seconds",
    "AI request duration in seconds",
    ["intent"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 60.0],
)

# 数据库连接池指标
db_pool_connections = Gauge(
    "db_pool_connections", "Database pool connections", ["state"]
)


# ============================================================
# Prometheus 中间件
# ============================================================


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Prometheus 指标收集中间件

    自动收集所有 HTTP 请求的指标
    """

    def __init__(self, app: FastAPI, excluded_paths: list = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/metrics", "/health"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 排除指标端点
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # 记录开始时间
        start_time = time.time()

        # 增加活跃请求数
        http_requests_active.inc()

        try:
            # 执行请求
            response = await call_next(request)

            # 计算持续时间
            duration = time.time() - start_time

            # 获取端点模式（简化路径）
            endpoint = self._get_endpoint_pattern(request)

            # 记录指标
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code,
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method, endpoint=endpoint
            ).observe(duration)

            return response

        finally:
            # 减少活跃请求数
            http_requests_active.dec()

    def _get_endpoint_pattern(self, request: Request) -> str:
        """将具体路径转换为模式（如 /tasks/123 -> /tasks/{id}）"""
        path = request.url.path

        # 简化常见路径模式
        patterns = [
            (r"/api/v1/tasks/\d+", "/api/v1/tasks/{id}"),
            (r"/api/v1/goals/\d+", "/api/v1/goals/{id}"),
            (r"/api/v1/users/\d+", "/api/v1/users/{id}"),
            (r"/api/v1/words/\d+", "/api/v1/words/{id}"),
            (r"/api/v1/reflection/logs/\d+", "/api/v1/reflection/logs/{id}"),
        ]

        import re

        for pattern, replacement in patterns:
            if re.match(pattern, path):
                return replacement

        return path


# ============================================================
# 业务指标记录函数
# ============================================================


def record_task_created():
    """记录任务创建"""
    tasks_created_total.inc()


def record_task_completed():
    """记录任务完成"""
    tasks_completed_total.inc()


def record_goal_created():
    """记录目标创建"""
    goals_created_total.inc()


def record_ai_request(intent: str, success: bool = True, duration: float = None):
    """
    记录 AI 请求

    Args:
        intent: 意图类型
        success: 是否成功
        duration: 持续时间（秒）
    """
    status = "success" if success else "failure"
    ai_requests_total.labels(intent=intent, status=status).inc()

    if duration is not None:
        ai_request_duration_seconds.labels(intent=intent).observe(duration)


# ============================================================
# 注册中间件和端点
# ============================================================


def register_prometheus(app: FastAPI):
    """
    注册 Prometheus 监控

    添加中间件和指标端点
    """
    # 添加中间件
    app.add_middleware(PrometheusMiddleware)

    # 添加指标端点
    @app.get("/metrics")
    async def metrics():
        """Prometheus 指标端点"""
        return StarletteResponse(content=generate_latest(), media_type="text/plain")
