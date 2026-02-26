"""
统一错误码体系和自定义异常

定义项目中使用的所有错误码，便于前端识别和处理。
"""

from enum import Enum
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import traceback


# ============================================================
# 错误码定义
# ============================================================


class ErrorCode(str, Enum):
    """
    错误码定义

    格式: ERR_模块_序号
    - 1xxx: 认证授权错误
    - 2xxx: 用户数据错误
    - 3xxx: 任务管理错误
    - 4xxx: 目标管理错误
    - 5xxx: Agent 智能体错误
    - 6xxx: LLM/AI 服务错误
    - 7xxx: 第三方服务错误
    - 8xxx: 数据库错误
    - 9xxx: 系统错误
    """

    # ============ 1xxx: 认证授权错误 ============
    ERR_AUTH_001 = "ERR_AUTH_001"  # 用户名已存在
    ERR_AUTH_002 = "ERR_AUTH_002"  # 用户名或密码错误
    ERR_AUTH_003 = "ERR_AUTH_003"  # Token 过期
    ERR_AUTH_004 = "ERR_AUTH_004"  # Token 无效
    ERR_AUTH_005 = "ERR_AUTH_005"  # 缺少认证信息
    ERR_AUTH_006 = "ERR_AUTH_006"  # 密码强度不足

    # ============ 2xxx: 用户数据错误 ============
    ERR_USER_001 = "ERR_USER_001"  # 用户不存在
    ERR_USER_002 = "ERR_USER_002"  # 用户信息更新失败
    ERR_USER_003 = "ERR_USER_003"  # 推送 Token 无效

    # ============ 3xxx: 任务管理错误 ============
    ERR_TASK_001 = "ERR_TASK_001"  # 任务不存在
    ERR_TASK_002 = "ERR_TASK_002"  # 任务创建失败
    ERR_TASK_003 = "ERR_TASK_003"  # 任务更新失败
    ERR_TASK_004 = "ERR_TASK_004"  # 任务删除失败
    ERR_TASK_005 = "ERR_TASK_005"  # 任务状态无效
    ERR_TASK_006 = "ERR_TASK_006"  # 任务权限不足
    ERR_TASK_007 = "ERR_TASK_007"  # 任务依赖不存在

    # ============ 4xxx: 目标管理错误 ============
    ERR_GOAL_001 = "ERR_GOAL_001"  # 目标不存在
    ERR_GOAL_002 = "ERR_GOAL_002"  # 目标创建失败
    ERR_GOAL_003 = "ERR_GOAL_003"  # 目标更新失败
    ERR_GOAL_004 = "ERR_GOAL_004"  # 目标删除失败
    ERR_GOAL_005 = "ERR_GOAL_005"  # 目标权限不足

    # ============ 5xxx: Agent 智能体错误 ============
    ERR_AGENT_001 = "ERR_AGENT_001"  # Agent 初始化失败
    ERR_AGENT_002 = "ERR_AGENT_002"  # 会话不存在
    ERR_AGENT_003 = "ERR_AGENT_003"  # 会话已过期
    ERR_AGENT_004 = "ERR_AGENT_004"  # 意图识别失败
    ERR_AGENT_005 = "ERR_AGENT_005"  # Skill 不存在
    ERR_AGENT_006 = "ERR_AGENT_006"  # Skill 执行失败
    ERR_AGENT_007 = "ERR_AGENT_007"  # Tool 调用失败
    ERR_AGENT_008 = "ERR_AGENT_008"  # 记忆存储失败

    # ============ 6xxx: LLM/AI 服务错误 ============
    ERR_LLM_001 = "ERR_LLM_001"  # LLM API 调用失败
    ERR_LLM_002 = "ERR_LLM_002"  # LLM 响应格式错误
    ERR_LLM_003 = "ERR_LLM_003"  # LLM 超时
    ERR_LLM_004 = "ERR_LLM_004"  # LLM 频率限制
    ERR_LLM_005 = "ERR_LLM_005"  # LLM API Key 无效
    ERR_LLM_006 = "ERR_LLM_006"  # Embedding 生成失败
    ERR_LLM_007 = "ERR_LLM_007"  # 所有 Embedding 提供商都失败

    # ============ 7xxx: 第三方服务错误 ============
    ERR_EXT_001 = "ERR_EXT_001"  # 搜索服务不可用
    ERR_EXT_002 = "ERR_EXT_002"  # 推送服务不可用
    ERR_EXT_003 = "ERR_EXT_003"  # 缓存服务不可用
    ERR_EXT_004 = "ERR_EXT_004"  # 数据库连接失败

    # ============ 8xxx: 数据库错误 ============
    ERR_DB_001 = "ERR_DB_001"  # 数据库连接失败
    ERR_DB_002 = "ERR_DB_002"  # 数据库操作失败
    ERR_DB_003 = "ERR_DB_003"  # 数据不存在

    # ============ 9xxx: 系统错误 ============
    ERR_SYS_001 = "ERR_SYS_001"  # 未知错误
    ERR_SYS_002 = "ERR_SYS_002"  # 参数验证失败
    ERR_SYS_003 = "ERR_SYS_003"  # 内部服务器错误
    ERR_SYS_004 = "ERR_SYS_004"  # 服务暂不可用

    @property
    def http_status(self) -> int:
        """获取 HTTP 状态码"""
        mapping = {
            "ERR_AUTH": 401,
            "ERR_USER": 400,
            "ERR_TASK": 400,
            "ERR_GOAL": 400,
            "ERR_AGENT": 400,
            "ERR_LLM": 502,
            "ERR_EXT": 503,
            "ERR_DB": 500,
            "ERR_SYS": 500,
        }
        prefix = self.value.split("_")[1]
        return mapping.get(prefix, 500)

    @property
    def message(self) -> str:
        """获取默认错误消息"""
        messages = {
            "ERR_AUTH_001": "用户名已存在",
            "ERR_AUTH_002": "用户名或密码错误",
            "ERR_AUTH_003": "登录已过期，请重新登录",
            "ERR_AUTH_004": "无效的登录凭证",
            "ERR_AUTH_005": "缺少认证信息",
            "ERR_AUTH_006": "密码强度不足",
            "ERR_USER_001": "用户不存在",
            "ERR_USER_002": "用户信息更新失败",
            "ERR_USER_003": "推送 Token 无效",
            "ERR_TASK_001": "任务不存在",
            "ERR_TASK_002": "任务创建失败",
            "ERR_TASK_003": "任务更新失败",
            "ERR_TASK_004": "任务删除失败",
            "ERR_TASK_005": "无效的任务状态",
            "ERR_TASK_006": "无权操作此任务",
            "ERR_TASK_007": "依赖的任务不存在",
            "ERR_GOAL_001": "目标不存在",
            "ERR_GOAL_002": "目标创建失败",
            "ERR_GOAL_003": "目标更新失败",
            "ERR_GOAL_004": "目标删除失败",
            "ERR_GOAL_005": "无权操作此目标",
            "ERR_AGENT_001": "Agent 初始化失败",
            "ERR_AGENT_002": "会话不存在",
            "ERR_AGENT_003": "会话已过期",
            "ERR_AGENT_004": "无法理解您的请求",
            "ERR_AGENT_005": "指定的技能不存在",
            "ERR_AGENT_006": "技能执行失败",
            "ERR_AGENT_007": "工具调用失败",
            "ERR_AGENT_008": "记忆存储失败",
            "ERR_LLM_001": "AI 服务暂时不可用",
            "ERR_LLM_002": "AI 响应格式错误",
            "ERR_LLM_003": "AI 服务响应超时",
            "ERR_LLM_004": "AI 服务请求过于频繁",
            "ERR_LLM_005": "AI API Key 配置错误",
            "ERR_LLM_006": "向量嵌入生成失败",
            "ERR_LLM_007": "所有向量服务提供商均不可用",
            "ERR_EXT_001": "搜索服务暂时不可用",
            "ERR_EXT_002": "推送服务暂时不可用",
            "ERR_EXT_003": "缓存服务暂时不可用",
            "ERR_EXT_004": "数据库连接失败",
            "ERR_DB_001": "数据库连接失败",
            "ERR_DB_002": "数据库操作失败",
            "ERR_DB_003": "请求的数据不存在",
            "ERR_SYS_001": "发生未知错误",
            "ERR_SYS_002": "请求参数验证失败",
            "ERR_SYS_003": "服务器内部错误",
            "ERR_SYS_004": "服务暂不可用，请稍后重试",
        }
        return messages.get(self.value, "未知错误")


# ============================================================
# 自定义异常类
# ============================================================


class AppException(Exception):
    """应用基础异常类"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: ErrorCode = None,
        details: dict = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    """资源不存在异常"""

    def __init__(
        self,
        resource: str,
        resource_id: int | str = None,
        error_code: ErrorCode = None,
    ):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"

        # 根据资源类型确定错误码
        if not error_code:
            resource_codes = {
                "user": ErrorCode.ERR_USER_001,
                "task": ErrorCode.ERR_TASK_001,
                "goal": ErrorCode.ERR_GOAL_001,
            }
            error_code = resource_codes.get(resource.lower(), ErrorCode.ERR_DB_003)

        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code,
        )


class ForbiddenException(AppException):
    """权限不足异常"""

    def __init__(
        self,
        message: str = "无权访问此资源",
        error_code: ErrorCode = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code or ErrorCode.ERR_TASK_006,
        )


class UnauthorizedException(AppException):
    """未授权异常"""

    def __init__(
        self,
        message: str = "请先登录",
        error_code: ErrorCode = ErrorCode.ERR_AUTH_005,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
        )


class BadRequestException(AppException):
    """请求参数错误异常"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.ERR_SYS_002,
        details: dict = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
            details=details,
        )


class DatabaseException(AppException):
    """数据库操作异常"""

    def __init__(
        self,
        message: str = "数据库操作失败",
        error_code: ErrorCode = ErrorCode.ERR_DB_002,
        details: dict = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            details=details,
        )


class ServiceUnavailableException(AppException):
    """服务不可用异常"""

    def __init__(
        self,
        message: str = "服务暂不可用",
        error_code: ErrorCode = ErrorCode.ERR_SYS_004,
        details: dict = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code=error_code,
            details=details,
        )


# ============================================================
# 异常处理器
# ============================================================


async def app_exception_handler(request: Request, exc: AppException):
    """应用异常处理器"""
    content = {
        "success": False,
        "error": exc.message,
        "error_code": exc.error_code.value if exc.error_code else None,
    }
    if exc.details:
        content["details"] = exc.details

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """参数验证异常处理器"""
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "请求参数验证失败",
            "error_code": ErrorCode.ERR_SYS_002.value,
            "details": {"errors": errors},
        },
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """SQLAlchemy 异常处理器"""
    error_message = "数据库操作失败"
    error_code = ErrorCode.ERR_DB_002

    if isinstance(exc, IntegrityError):
        error_message = "数据冲突，请检查输入"
        error_code = ErrorCode.ERR_DB_002

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": error_message,
            "error_code": error_code.value,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    import logging

    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "服务器内部错误",
            "error_code": ErrorCode.ERR_SYS_003.value,
        },
    )


def register_exception_handlers(app):
    """注册所有异常处理器"""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
