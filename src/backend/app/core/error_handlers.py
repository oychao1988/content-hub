"""
全局错误处理器
"""
import uuid
import traceback
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.modules.shared.schemas.api import ApiResponse, ErrorDetail
from app.utils.custom_logger import log


# 错误码常量定义
class ErrorCode:
    """错误码常量"""

    # 通用错误 (1xxx)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # 认证授权错误 (2xxx)
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    CREDENTIALS_INVALID = "CREDENTIALS_INVALID"
    PERMISSION_DENIED = "PERMISSION_DENIED"

    # 资源错误 (3xxx)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    RESOURCE_LOCKED = "RESOURCE_LOCKED"

    # 业务逻辑错误 (4xxx)
    BUSINESS_ERROR = "BUSINESS_ERROR"
    OPERATION_FAILED = "OPERATION_FAILED"
    INVALID_STATE = "INVALID_STATE"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"

    # 外部服务错误 (5xxx)
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    EXTERNAL_SERVICE_TIMEOUT = "EXTERNAL_SERVICE_TIMEOUT"
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"

    # Content-Creator 错误 (51xx)
    CREATOR_CLI_NOT_FOUND = "CREATOR_CLI_NOT_FOUND"
    CREATOR_EXECUTION_FAILED = "CREATOR_EXECUTION_FAILED"
    CREATOR_TIMEOUT = "CREATOR_TIMEOUT"
    CREATOR_INVALID_RESPONSE = "CREATOR_INVALID_RESPONSE"

    # Content-Publisher 错误 (52xx)
    PUBLISHER_API_ERROR = "PUBLISHER_API_ERROR"
    PUBLISHER_TIMEOUT = "PUBLISHER_TIMEOUT"
    PUBLISHER_UNAUTHORIZED = "PUBLISHER_UNAUTHORIZED"
    PUBLISHER_INVALID_RESPONSE = "PUBLISHER_INVALID_RESPONSE"

    # Tavily API 错误 (53xx)
    TAVILY_API_ERROR = "TAVILY_API_ERROR"
    TAVILY_QUOTA_EXCEEDED = "TAVILY_QUOTA_EXCEEDED"
    TAVILY_INVALID_KEY = "TAVILY_INVALID_KEY"

    # 数据库错误 (6xxx)
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_QUERY_ERROR = "DATABASE_QUERY_ERROR"

    # 文件操作错误 (7xxx)
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_UPLOAD_FAILED = "FILE_UPLOAD_FAILED"
    FILE_SIZE_EXCEEDED = "FILE_SIZE_EXCEEDED"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"


def generate_request_id() -> str:
    """生成请求 ID"""
    return f"req_{uuid.uuid4().hex[:16]}"


def sanitize_error_details(details: Dict[str, Any]) -> Dict[str, Any]:
    """脱敏敏感信息"""
    sensitive_keys = {
        "password", "token", "secret", "key", "authorization",
        "api_key", "access_token", "refresh_token"
    }

    sanitized = {}
    for key, value in details.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        else:
            sanitized[key] = value

    return sanitized


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    HTTP异常处理器

    将所有HTTP异常转换为统一响应格式
    """
    # 优先使用中间件生成的请求 ID
    request_id = getattr(request.state, "request_id", None) or generate_request_id()

    # 记录错误日志
    log.warning(
        f"HTTP Exception [{request_id}]: {exc.status_code} - {exc.detail} | "
        f"Path: {request.url.path} | Method: {request.method}"
    )

    # 映射错误码
    error_code_map = {
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        405: ErrorCode.METHOD_NOT_ALLOWED,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
    }

    error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR)

    error = ErrorDetail(
        code=error_code,
        message=str(exc.detail),
        details=None
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": error.dict(),
            "requestId": request_id
        }
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    请求校验异常处理器

    将请求参数校验异常转换为统一响应格式
    """
    # 优先使用中间件生成的请求 ID
    request_id = getattr(request.state, "request_id", None) or generate_request_id()

    # 构建详细的错误信息
    error_details = {}
    for error in exc.errors():
        location = error["loc"]
        field = location[-1] if len(location) > 0 else "unknown"
        if isinstance(field, int):
            field = f"item_{field}"

        error_msg = error["msg"]
        error_type = error["type"]

        # 提供更友好的错误提示
        if error_type == "missing":
            error_msg = f"字段 '{field}' 是必填项"
        elif error_type == "type_error.integer":
            error_msg = f"字段 '{field}' 必须是整数"
        elif error_type == "type_error.str":
            error_msg = f"字段 '{field}' 必须是字符串"
        elif error_type == "type_error.email":
            error_msg = f"字段 '{field}' 必须是有效的邮箱地址"
        elif error_type == "value_error.email.not_valid":
            error_msg = f"字段 '{field}' 的邮箱格式不正确"

        error_details[field] = error_msg

    # 记录错误日志
    log.warning(
        f"Validation Error [{request_id}]: {len(exc.errors())} field(s) | "
        f"Path: {request.url.path} | Method: {request.method} | "
        f"Details: {error_details}"
    )

    error = ErrorDetail(
        code=ErrorCode.VALIDATION_ERROR,
        message="输入数据验证失败",
        details=error_details
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "data": None,
            "error": error.dict(),
            "requestId": request_id
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器

    将所有未处理的异常转换为统一响应格式
    """
    # 优先使用中间件生成的请求 ID
    request_id = getattr(request.state, "request_id", None) or generate_request_id()

    # 获取异常堆栈信息
    error_traceback = traceback.format_exc()

    # 记录完整的错误日志
    log.error(
        f"Unhandled Exception [{request_id}]: {type(exc).__name__} - {str(exc)} | "
        f"Path: {request.url.path} | Method: {request.method}\n"
        f"Stack Trace:\n{error_traceback}"
    )

    # 检查是否是特定的业务异常
    error_code = ErrorCode.INTERNAL_SERVER_ERROR
    error_message = "服务器内部错误，请稍后重试"

    # 如果异常有 code 属性，使用它
    if hasattr(exc, "code"):
        error_code = exc.code
    if hasattr(exc, "message"):
        error_message = exc.message

    # 在开发模式下返回详细的错误信息
    details = None
    if not hasattr(request.app.state, "production") or not request.app.state.production:
        details = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)
        }

    error = ErrorDetail(
        code=error_code,
        message=error_message,
        details=details
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "error": error.dict(),
            "requestId": request_id
        }
    )


async def business_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    业务异常处理器

    处理自定义的业务异常
    """
    # 优先使用中间件生成的请求 ID
    request_id = getattr(request.state, "request_id", None) or generate_request_id()

    # 获取异常信息
    error_code = getattr(exc, "code", ErrorCode.BUSINESS_ERROR)
    error_message = getattr(exc, "message", "业务处理失败")
    error_details = getattr(exc, "details", None)
    status_code = getattr(exc, "status_code", status.HTTP_400_BAD_REQUEST)

    # 脱敏处理
    if error_details and isinstance(error_details, dict):
        error_details = sanitize_error_details(error_details)

    # 记录错误日志
    log.warning(
        f"Business Exception [{request_id}]: {error_code} - {error_message} | "
        f"Path: {request.url.path} | Method: {request.method} | "
        f"Status: {status_code}"
    )

    error = ErrorDetail(
        code=error_code,
        message=error_message,
        details=error_details
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "error": error.dict(),
            "requestId": request_id
        }
    )
