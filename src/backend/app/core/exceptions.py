from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.modules.shared.schemas.api import ApiResponse, ErrorDetail


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    HTTP异常处理器

    将所有HTTP异常转换为统一响应格式
    """
    error = ErrorDetail(
        code=f"HTTP_{exc.status_code}", message=str(exc.detail), details=None
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(success=False, data=None, error=error, meta=None).dict(),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    请求校验异常处理器

    将请求参数校验异常转换为统一响应格式
    """
    error_details = {}
    for error in exc.errors():
        location = error["loc"]
        field = location[-1] if len(location) > 0 else "unknown"
        if isinstance(field, int):
            field = f"item_{field}"
        error_details[field] = error["msg"]

    error = ErrorDetail(
        code="VALIDATION_ERROR", message="输入数据验证失败", details=error_details
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ApiResponse(success=False, data=None, error=error, meta=None).dict(),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器

    将所有未处理的异常转换为统一响应格式
    """
    error = ErrorDetail(code="INTERNAL_SERVER_ERROR", message=str(exc), details=None)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiResponse(success=False, data=None, error=error, meta=None).dict(),
    )
