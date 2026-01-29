from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.shared.schemas.api import ApiResponse
from app.modules.system.services import system_service
from app.modules.system.schemas import HealthResponse, SystemInfoResponse, MetricsResponse

router = APIRouter()


@router.get("/health", response_model=ApiResponse[HealthResponse])
async def get_health(db: Session = Depends(get_db)) -> ApiResponse[HealthResponse]:
    """
    获取系统健康状态

    检查数据库、Redis、外部服务等的健康状态
    """
    health_data = system_service.get_health_status(db)
    return ApiResponse(success=True, data=health_data)


@router.get("/info", response_model=ApiResponse[SystemInfoResponse])
async def get_system_info() -> ApiResponse[SystemInfoResponse]:
    """
    获取系统信息

    返回版本、Python版本、环境等信息
    """
    info_data = system_service.get_system_info()
    return ApiResponse(success=True, data=info_data)


@router.get("/metrics", response_model=ApiResponse[MetricsResponse])
async def get_metrics(db: Session = Depends(get_db)) -> ApiResponse[MetricsResponse]:
    """
    获取系统指标

    返回请求数、活跃用户数、缓存统计等指标
    """
    metrics_data = system_service.get_metrics(db)
    return ApiResponse(success=True, data=metrics_data)
