"""
结构化日志配置

提供统一的日志格式和配置，支持：
- JSON 格式输出（便于日志收集）
- 彩色控制台输出（开发环境）
- 区分不同级别的日志处理
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any

from app.config import settings
from app.utils.timezone import get_utc_now


class StructuredLogFormatter(logging.Formatter):
    """
    结构化日志格式化器

    输出 JSON 格式日志，包含:
    - timestamp: 时间戳
    - level: 日志级别
    - logger: 日志记录器名称
    - message: 日志消息
    - extra: 额外字段
    """

    def __init__(self, use_colors: bool = False):
        super().__init__()
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        # 构建基础日志结构
        log_data = {
            "timestamp": get_utc_now().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外字段（通过 extra 传递）
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        # 添加请求ID（如果存在）
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # 开发环境使用彩色输出
        if self.use_colors:
            return self._format_color(log_data, record.levelno)

        # 生产环境输出 JSON
        return json.dumps(log_data, ensure_ascii=False, default=str)

    def _format_color(self, log_data: dict, level: int) -> str:
        """彩色格式化（开发环境）"""
        colors = {
            logging.DEBUG: "\033[36m",  # 青色
            logging.INFO: "\033[32m",  # 绿色
            logging.WARNING: "\033[33m",  # 黄色
            logging.ERROR: "\033[31m",  # 红色
            logging.CRITICAL: "\033[35m",  # 紫色
        }
        reset = "\033[0m"

        color = colors.get(level, "")
        level_name = log_data["level"]

        return (
            f"{color}[{log_data['timestamp']}] "
            f"{level_name:8s} "
            f"{log_data['logger']:30s} "
            f"{log_data['message']}{reset}"
        )


class LoggerAdapter(logging.LoggerAdapter):
    """
    自定义日志适配器

    支持添加额外的上下文信息（如 user_id, request_id 等）
    """

    def process(self, msg: str, kwargs: dict):
        # 将 extra_data 传递给 LogRecord
        if "extra_data" in kwargs:
            extra = kwargs.pop("extra_data")
            kwargs["extra"] = {"extra_data": extra}
        return msg, kwargs


def setup_logging():
    """
    配置全局日志系统

    开发环境: 彩色控制台输出
    生产环境: JSON 格式输出
    """
    # 根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # 清除现有处理器
    root_logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # 选择格式化器
    formatter = StructuredLogFormatter(use_colors=settings.DEBUG)
    console_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)

    # 设置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # 记录启动日志
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured", extra={"extra_data": {"debug_mode": settings.DEBUG}}
    )


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称（通常使用 __name__）

    Returns:
        配置好的日志记录器
    """
    return logging.getLogger(name)


def get_structured_logger(name: str) -> LoggerAdapter:
    """
    获取结构化日志记录器

    支持添加额外的上下文信息。

    Example:
        logger = get_structured_logger(__name__)
        logger.info("User action", extra_data={"user_id": 123, "action": "create"})
    """
    base_logger = logging.getLogger(name)
    return LoggerAdapter(base_logger, {})


# 便捷函数：快速记录结构化日志
def log_user_action(logger: logging.Logger, user_id: int, action: str, **kwargs):
    """记录用户操作日志"""
    extra = {"user_id": user_id, "action": action, **kwargs}
    logger.info(f"User action: {action}", extra_data=extra)


def log_api_request(logger: logging.Logger, method: str, path: str, **kwargs):
    """记录 API 请求日志"""
    extra = {"method": method, "path": path, **kwargs}
    logger.info(f"API request: {method} {path}", extra_data=extra)


def log_error_with_context(logger: logging.Logger, error: Exception, **kwargs):
    """记录错误日志（含上下文）"""
    extra = {"error_type": type(error).__name__, **kwargs}
    logger.error(f"Error: {str(error)}", extra_data=extra, exc_info=True)
