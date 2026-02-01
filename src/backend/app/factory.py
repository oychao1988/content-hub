"""
ContentHub 应用工厂
"""
from __future__ import annotations

import time
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import (
    BaseAppException,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.error_handlers import business_exception_handler
from app.core.middleware import (
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    ErrorContextMiddleware
)
from app.core.module_system.loader import load_modules, run_shutdown, run_startup
from app.db.sql_db import init_db
from app.utils.custom_logger import log


class ApiResponse(BaseModel):
    """统一 API 响应格式"""

    success: bool
    data: Dict | None = None
    message: str | None = None
    error: str | None = None


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""

    app = FastAPI(
        title=settings.APP_NAME,
        description="ContentHub 内容运营管理系统 API",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    )

    # CORS 配置
    if hasattr(settings, "CORS_ORIGINS"):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # 添加自定义中间件（注意顺序：后添加的先执行）
    app.add_middleware(ErrorContextMiddleware)  # 最内层
    app.add_middleware(RequestLoggingMiddleware)  # 中间层
    app.add_middleware(RequestIDMiddleware)  # 最外层

    # 异常处理器
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(BaseAppException, business_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # 加载业务模块
    modules = load_modules(app, settings)
    app.state.modules = modules

    # 为 customer 模块添加复数形式路由别名（兼容前端调用）
    # 前端调用 /api/v1/customers/，后端实际路径是 /api/v1/customer/
    for module in modules:
        if module.name == "customer":
            # 添加 /api/v1/customers 别名
            app.include_router(
                module.router,
                prefix=f"{settings.API_V1_PREFIX}/customers",
                tags=["customers"]
            )
            log.info("✅ 已为 customer 模块添加复数路由别名 /api/v1/customers")
            break

    # 启动事件
    @app.on_event("startup")
    async def startup() -> None:
        """应用启动时执行"""
        log.info(f"🚀 启动 {settings.APP_NAME} v{settings.APP_VERSION}")

        # 运行模块启动钩子
        await run_startup(modules, app)

        # 初始化数据库
        if getattr(settings, "SQL_AUTO_INIT", True):
            init_db()
            log.info("✅ 数据库初始化完成")

        # 启动任务调度器
        if settings.SCHEDULER_ENABLED:
            from app.services.scheduler_service import scheduler_service

            scheduler_service.start()
            log.info("✅ 任务调度器已启动")

    # 关闭事件
    @app.on_event("shutdown")
    async def shutdown() -> None:
        """应用关闭时执行"""
        log.info("🛑 正在关闭应用...")

        # 停止任务调度器
        if settings.SCHEDULER_ENABLED:
            from app.services.scheduler_service import scheduler_service

            scheduler_service.shutdown()
            log.info("✅ 任务调度器已停止")

        # 运行模块关闭钩子
        await run_shutdown(modules, app)

        log.info("✅ 应用已关闭")

    # 健康检查接口
    @app.get("/", tags=["健康检查"])
    def read_root():
        """根路径健康检查"""
        return ApiResponse(
            success=True,
            data={
                "app": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "api_docs": "/docs",
                "api_v1": settings.API_V1_PREFIX,
            },
        )

    @app.get("/health", tags=["健康检查"])
    def health_check():
        """健康检查接口"""
        return {
            "status": "ok",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

    return app
