from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.logging_config import setup_logging
from app.routers import (
    auth,
    tools,
    skills,
    ai,
    execution,
    tasks,
    goals,
    reflection,
    fixed_schedules,
    friends,
    comments,
    users,
    words,
    feedback,
)
from app.agent.router import router as agent_router
from app.scheduler import start_scheduler, shutdown_scheduler
from app.exceptions import register_exception_handlers
from app.middleware.security import register_security_middlewares
from app.monitoring.prometheus import register_prometheus


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title="Plan Agent Backend",
    description="A FastAPI backend for intelligent task planning with AI agents",
    version="1.0.0",
    lifespan=lifespan,
)

# 初始化日志
setup_logging()

# 注册安全中间件
register_security_middlewares(
    app,
    cors_origins=settings.CORS_ORIGINS,
    rate_limit_per_minute=60,
    rate_limit_per_hour=1000,
    max_request_size=1024 * 1024,  # 1MB
)

# 注册异常处理器
register_exception_handlers(app)

# 注册 Prometheus 监控
register_prometheus(app)

# 注册路由
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(tools.router, prefix=settings.API_PREFIX)
app.include_router(skills.router, prefix=settings.API_PREFIX)
# AI Router - 旧版对话式计划创建系统 (逐步迁移到 Agent)
# TODO: 未来将废弃 ai router，统一使用 agent router
app.include_router(ai.router, prefix=settings.API_PREFIX)
app.include_router(agent_router, prefix=settings.API_PREFIX)
app.include_router(execution.router, prefix=settings.API_PREFIX)
app.include_router(tasks.router, prefix=settings.API_PREFIX)
app.include_router(goals.router, prefix=settings.API_PREFIX)
app.include_router(reflection.router, prefix=settings.API_PREFIX)
app.include_router(fixed_schedules.router, prefix=settings.API_PREFIX)
app.include_router(friends.router, prefix=settings.API_PREFIX)
app.include_router(comments.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)
app.include_router(words.router, prefix=settings.API_PREFIX)
app.include_router(feedback.router, prefix=settings.API_PREFIX)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Plan Agent Backend is running"}


@app.get("/health/detailed")
async def detailed_health_check():
    """详细健康检查"""
    import subprocess
    import sys

    health_status = {"status": "healthy", "checks": {}}

    # 检查 Python 版本
    health_status["checks"]["python"] = {"version": sys.version, "status": "ok"}

    # 检查数据库连接
    try:
        from sqlalchemy import text
        from app.dependencies import engine

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {"status": "ok"}
    except Exception as e:
        health_status["checks"]["database"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    return health_status
