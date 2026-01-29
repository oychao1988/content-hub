"""
请求中间件
包括请求 ID 追踪、请求日志等
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.utils.custom_logger import log


class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求 ID 中间件

    为每个请求生成唯一 ID，用于追踪和调试
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. 从请求头获取或生成新的请求 ID
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:16]}"

        # 2. 将请求 ID 存储到 request.state
        request.state.request_id = request_id

        # 3. 处理请求
        response = await call_next(request)

        # 4. 将请求 ID 添加到响应头
        response.headers["X-Request-ID"] = request_id

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件

    记录所有请求和响应的详细信息
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # 获取请求 ID
        request_id = getattr(request.state, "request_id", "unknown")

        # 记录请求开始
        log.info(
            f"Request started [{request_id}] {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        # 处理请求
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # 记录请求完成
            log_level = log.warning if process_time > 3.0 else log.info
            log_level(
                f"Request completed [{request_id}] {request.method} {request.url.path} "
                f"status={response.status_code} duration={process_time:.3f}s"
            )

            # 添加响应时间到响应头
            response.headers["X-Process-Time"] = f"{process_time:.3f}"

            return response

        except Exception as e:
            process_time = time.time() - start_time
            log.error(
                f"Request failed [{request_id}] {request.method} {request.url.path} "
                f"error={str(e)} duration={process_time:.3f}s"
            )
            raise


class ErrorContextMiddleware(BaseHTTPMiddleware):
    """错误上下文中间件

    为错误处理器提供额外的上下文信息
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 存储请求开始时间（用于计算处理时间）
        request.state.start_time = time.time()

        # 存储请求信息（用于错误日志）
        request.state.request_info = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_host": request.client.host if request.client else "unknown",
        }

        return await call_next(request)
