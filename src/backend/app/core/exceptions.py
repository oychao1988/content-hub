"""
自定义异常类
"""
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.modules.shared.schemas.api import ApiResponse, ErrorDetail
from app.core.error_handlers import ErrorCode


# ==================== 异常基类 ====================

class BaseAppException(Exception):
    """
    应用异常基类

    所有自定义异常都应该继承此类
    """

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.BUSINESS_ERROR,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.message = message
        self.code = code
        self.details = details
        self.status_code = status_code
        super().__init__(self.message)


# ==================== 业务异常类 ====================

class BusinessException(BaseAppException):
    """
    通用业务异常

    用于处理一般的业务逻辑错误
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        code: str = ErrorCode.BUSINESS_ERROR
    ):
        super().__init__(
            message=message,
            code=code,
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ResourceNotFoundException(BaseAppException):
    """
    资源未找到异常

    用于请求的资源不存在的情况
    """

    def __init__(
        self,
        resource_name: str = "资源",
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource_name}不存在"
        if resource_id:
            message += f" (ID: {resource_id})"

        _details = details or {}
        if resource_id:
            _details["resource_id"] = resource_id

        super().__init__(
            message=message,
            code=ErrorCode.RESOURCE_NOT_FOUND,
            details=_details,
            status_code=status.HTTP_404_NOT_FOUND
        )


class ResourceAlreadyExistsException(BaseAppException):
    """
    资源已存在异常

    用于尝试创建已存在的资源
    """

    def __init__(
        self,
        resource_name: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource_name}已存在"
        if resource_id:
            message += f" (ID: {resource_id})"

        _details = details or {}
        if resource_id:
            _details["resource_id"] = resource_id

        super().__init__(
            message=message,
            code=ErrorCode.RESOURCE_ALREADY_EXISTS,
            details=_details,
            status_code=status.HTTP_409_CONFLICT
        )


class PermissionDeniedException(BaseAppException):
    """
    权限不足异常

    用于用户没有权限执行某操作
    """

    def __init__(
        self,
        message: str = "您没有权限执行此操作",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.PERMISSION_DENIED,
            details=details,
            status_code=status.HTTP_403_FORBIDDEN
        )


class InvalidStateException(BaseAppException):
    """
    无效状态异常

    用于资源状态不满足操作条件
    """

    def __init__(
        self,
        message: str,
        current_state: Optional[str] = None,
        required_state: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        _details = details or {}
        if current_state:
            _details["current_state"] = current_state
        if required_state:
            _details["required_state"] = required_state

        super().__init__(
            message=message,
            code=ErrorCode.INVALID_STATE,
            details=_details,
            status_code=status.HTTP_400_BAD_REQUEST
        )


# ==================== 外部服务异常类 ====================

class ExternalServiceException(BaseAppException):
    """
    外部服务异常基类
    """

    def __init__(
        self,
        service_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        code: str = ErrorCode.EXTERNAL_SERVICE_ERROR
    ):
        _details = details or {}
        _details["service"] = service_name

        super().__init__(
            message=message,
            code=code,
            details=_details,
            status_code=status.HTTP_502_BAD_GATEWAY
        )


class ServiceTimeoutException(ExternalServiceException):
    """
    服务超时异常
    """

    def __init__(
        self,
        service_name: str,
        timeout: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{service_name} 服务超时"
        if timeout:
            message += f" (超时时间: {timeout}秒)"

        _details = details or {}
        if timeout:
            _details["timeout"] = timeout

        super().__init__(
            service_name=service_name,
            message=message,
            details=_details,
            code=ErrorCode.EXTERNAL_SERVICE_TIMEOUT
        )


class ServiceUnavailableException(ExternalServiceException):
    """
    服务不可用异常
    """

    def __init__(
        self,
        service_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            service_name=service_name,
            message=f"{service_name} 服务暂时不可用",
            details=details,
            code=ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE
        )


# ==================== Content-Creator 异常 ====================

class CreatorException(BaseAppException):
    """Content-Creator 服务异常"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        code: str = ErrorCode.CREATOR_EXECUTION_FAILED
    ):
        super().__init__(
            message=message,
            code=code,
            details=details,
            status_code=status.HTTP_502_BAD_GATEWAY
        )


class CreatorCLINotFoundException(CreatorException):
    """Content-Creator CLI 未找到"""

    def __init__(self, cli_path: str):
        super().__init__(
            message=f"Content-Creator CLI 未找到: {cli_path}",
            details={"cli_path": cli_path},
            code=ErrorCode.CREATOR_CLI_NOT_FOUND
        )


class CreatorTimeoutException(CreatorException):
    """Content-Creator 执行超时"""

    def __init__(self, timeout: int):
        super().__init__(
            message=f"Content-Creator 执行超时 ({timeout}秒)",
            details={"timeout": timeout},
            code=ErrorCode.CREATOR_TIMEOUT
        )


class CreatorInvalidResponseException(CreatorException):
    """Content-Creator 响应格式错误"""

    def __init__(self, response: str):
        super().__init__(
            message="Content-Creator 返回了无效的响应格式",
            details={"response_preview": response[:200]},
            code=ErrorCode.CREATOR_INVALID_RESPONSE
        )


# ==================== Content-Publisher 异常 ====================

class PublisherException(BaseAppException):
    """Content-Publisher 服务异常"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        code: str = ErrorCode.PUBLISHER_API_ERROR,
        status_code: int = status.HTTP_502_BAD_GATEWAY
    ):
        super().__init__(
            message=message,
            code=code,
            details=details,
            status_code=status_code
        )


class PublisherTimeoutException(PublisherException):
    """Content-Publisher 请求超时"""

    def __init__(self, timeout: float):
        super().__init__(
            message=f"Content-Publisher 请求超时 ({timeout}秒)",
            details={"timeout": timeout},
            code=ErrorCode.PUBLISHER_TIMEOUT
        )


class PublisherUnauthorizedException(PublisherException):
    """Content-Publisher 认证失败"""

    def __init__(self):
        PublisherException.__init__(
            self,
            message="Content-Publisher API 认证失败，请检查 API Key",
            code=ErrorCode.PUBLISHER_UNAUTHORIZED,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


# ==================== 数据库异常 ====================

class DatabaseException(BaseAppException):
    """数据库异常"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        code: str = ErrorCode.DATABASE_ERROR
    ):
        super().__init__(
            message=message,
            code=code,
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== 文件操作异常 ====================

class FileUploadException(BaseAppException):
    """文件上传异常"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.FILE_UPLOAD_FAILED,
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class FileSizeExceededException(FileUploadException):
    """文件大小超限异常"""

    def __init__(
        self,
        max_size: int,
        actual_size: int,
        filename: Optional[str] = None
    ):
        message = f"文件大小超出限制 (最大: {max_size / 1024 / 1024:.2f}MB)"
        if filename:
            message = f"文件 '{filename}' {message}"

        super().__init__(
            message=message,
            details={
                "max_size": max_size,
                "actual_size": actual_size,
                "filename": filename
            },
            code=ErrorCode.FILE_SIZE_EXCEEDED
        )


# ==================== 兼容旧版异常处理器 ====================
# 保留旧的异常处理器以保持向后兼容，但标记为 deprecated

async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    HTTP异常处理器 (Deprecated - 请使用 error_handlers.py 中的版本)

    将所有HTTP异常转换为统一响应格式
    """
    from app.core.error_handlers import http_exception_handler as new_handler
    return await new_handler(request, exc)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    请求校验异常处理器 (Deprecated - 请使用 error_handlers.py 中的版本)

    将请求参数校验异常转换为统一响应格式
    """
    from app.core.error_handlers import validation_exception_handler as new_handler
    return await new_handler(request, exc)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器 (Deprecated - 请使用 error_handlers.py 中的版本)

    将所有未处理的异常转换为统一响应格式
    """
    from app.core.error_handlers import general_exception_handler as new_handler
    return await new_handler(request, exc)
