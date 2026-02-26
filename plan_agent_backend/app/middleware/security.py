"""
安全中间件 - 速率限制、安全头、CORS 等
"""

import time
from collections import defaultdict
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


# ============================================================
# 速率限制
# ============================================================


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件

    基于内存的简单速率限制，生产环境建议使用 Redis
    """

    def __init__(
        self,
        app: FastAPI,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        # 简单内存存储，生产环境应使用 Redis
        self._request_counts = defaultdict(lambda: {"minute": [], "hour": []})

    def _clean_old_requests(self, timestamps: list, cutoff: float):
        """清理过期的时间戳"""
        now = time.time()
        return [ts for ts in timestamps if now - ts < cutoff]

    def _check_rate_limit(self, client_id: str) -> tuple[bool, str]:
        """检查速率限制"""
        now = time.time()
        minute_cutoff = now - 60
        hour_cutoff = now - 3600

        client_data = self._request_counts[client_id]

        # 清理过期记录
        client_data["minute"] = self._clean_old_requests(
            client_data["minute"], minute_cutoff
        )
        client_data["hour"] = self._clean_old_requests(client_data["hour"], hour_cutoff)

        # 检查每分钟限制
        if len(client_data["minute"]) >= self.requests_per_minute:
            return False, "请求过于频繁，请稍后再试 (每分钟限制)"

        # 检查每小时限制
        if len(client_data["hour"]) >= self.requests_per_hour:
            return False, "请求过于频繁，请稍后再试 (每小时限制)"

        # 记录请求
        client_data["minute"].append(now)
        client_data["hour"].append(now)

        return True, ""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 排除健康检查等不需要限速的路径
        if request.url.path in ["/health", "/health/detailed"]:
            return await call_next(request)

        # 获取客户端标识
        client_id = request.client.host if request.client else "unknown"

        # 检查速率限制
        allowed, message = self._check_rate_limit(client_id)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": message,
                    "error_code": "ERR_RATE_LIMIT",
                },
            )

        response = await call_next(request)

        # 添加速率限制响应头
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)

        return response


# ============================================================
# 安全响应头
# ============================================================


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全响应头中间件

    添加常见的安全响应头
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 防止 XSS 和内容类型嗅探
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 内容安全策略 (CSP)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.openai.com"
        )

        # 引用策略
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 权限策略
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response


# ============================================================
# 请求大小限制
# ============================================================


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    请求大小限制中间件
    """

    def __init__(self, app: FastAPI, max_size: int = 1024 * 1024):  # 默认 1MB
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查 Content-Length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=413,
                content={
                    "success": False,
                    "error": "请求体过大",
                    "error_code": "ERR_REQUEST_TOO_LARGE",
                },
            )

        return await call_next(request)


# ============================================================
# IP 黑名单
# ============================================================


class IPBlockListMiddleware(BaseHTTPMiddleware):
    """
    IP 黑名单中间件
    """

    def __init__(self, app: FastAPI, blocklist: set = None):
        super().__init__(app)
        self.blocklist = blocklist or set()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else None

        if client_ip in self.blocklist:
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error": "访问被拒绝",
                    "error_code": "ERR_IP_BLOCKED",
                },
            )

        return await call_next(request)


# ============================================================
# 注册所有安全中间件
# ============================================================


def register_security_middlewares(
    app: FastAPI,
    cors_origins: list = None,
    rate_limit_per_minute: int = 60,
    rate_limit_per_hour: int = 1000,
    max_request_size: int = 1024 * 1024,
    blocked_ips: set = None,
):
    """
    注册所有安全中间件

    参数:
        app: FastAPI 应用实例
        cors_origins: CORS 允许的源列表
        rate_limit_per_minute: 每分钟请求限制
        rate_limit_per_hour: 每小时请求限制
        max_request_size: 最大请求大小（字节）
        blocked_ips: IP 黑名单
    """

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins or ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 安全响应头
    app.add_middleware(SecurityHeadersMiddleware)

    # 速率限制
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=rate_limit_per_minute,
        requests_per_hour=rate_limit_per_hour,
    )

    # 请求大小限制
    app.add_middleware(
        RequestSizeLimitMiddleware,
        max_size=max_request_size,
    )

    # IP 黑名单
    if blocked_ips:
        app.add_middleware(
            IPBlockListMiddleware,
            blocklist=blocked_ips,
        )
