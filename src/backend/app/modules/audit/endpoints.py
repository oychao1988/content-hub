"""
Audit module endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.modules.shared.deps import get_current_user
from app.modules.shared.schemas.user import UserRead
from app.modules.audit.services import AuditService
from app.modules.audit.schemas import (
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogQueryParams,
    AuditLogExportRequest,
    AuditStatisticsResponse,
)
from app.core.permissions import require_permission, Permission
from app.utils.custom_logger import log

router = APIRouter()


@router.get("/logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    event_type: Optional[str] = Query(None, description="事件类型"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    result: Optional[str] = Query(None, description="结果：success/failure"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    search: Optional[str] = Query(None, description="搜索关键字"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """
    查询审计日志（分页）

    需要权限：audit:view
    """
    # 检查权限
    require_permission(current_user, Permission.AUDIT_VIEW)

    try:
        # 构建过滤条件
        filters = {}
        if event_type:
            filters["event_type"] = event_type
        if user_id:
            filters["user_id"] = user_id
        if result:
            filters["result"] = result

        # 解析日期
        from datetime import datetime
        if start_date:
            try:
                filters["start_date"] = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="开始日期格式错误，应为 YYYY-MM-DD")

        if end_date:
            try:
                filters["end_date"] = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="结束日期格式错误，应为 YYYY-MM-DD")

        if search:
            filters["search"] = search

        # 查询日志
        result_data = AuditService.get_audit_logs(db, filters, page, page_size)

        # 转换为响应格式
        logs_response = []
        for log_entry in result_data["logs"]:
            logs_response.append(AuditLogResponse(
                id=log_entry.id,
                timestamp=log_entry.timestamp,
                event_type=log_entry.event_type,
                event_name=AuditService.EVENT_TYPES.get(log_entry.event_type, log_entry.event_type),
                user_id=log_entry.user_id,
                ip_address=log_entry.ip_address,
                user_agent=log_entry.user_agent,
                result=log_entry.result,
                details=log_entry.details,
                created_at=log_entry.created_at
            ))

        return AuditLogListResponse(
            logs=logs_response,
            total=result_data["total"],
            page=page,
            page_size=page_size,
            total_pages=result_data["total_pages"]
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to get audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询审计日志失败: {str(e)}")


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log_detail(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """
    获取审计日志详情

    需要权限：audit:view
    """
    # 检查权限
    require_permission(current_user, Permission.AUDIT_VIEW)

    try:
        log_entry = AuditService.get_audit_log_by_id(db, log_id)

        if not log_entry:
            raise HTTPException(status_code=404, detail=f"审计日志 {log_id} 不存在")

        return AuditLogResponse(
            id=log_entry.id,
            timestamp=log_entry.timestamp,
            event_type=log_entry.event_type,
            event_name=AuditService.EVENT_TYPES.get(log_entry.event_type, log_entry.event_type),
            user_id=log_entry.user_id,
            ip_address=log_entry.ip_address,
            user_agent=log_entry.user_agent,
            result=log_entry.result,
            details=log_entry.details,
            created_at=log_entry.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to get audit log detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取审计日志详情失败: {str(e)}")


@router.post("/logs/export")
async def export_audit_logs(
    request_data: AuditLogExportRequest,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """
    导出审计日志

    需要权限：audit:export
    """
    # 检查权限
    require_permission(current_user, Permission.AUDIT_EXPORT)

    try:
        # 构建过滤条件
        filters = {}
        if request_data.event_type:
            filters["event_type"] = request_data.event_type
        if request_data.user_id:
            filters["user_id"] = request_data.user_id
        if request_data.result:
            filters["result"] = request_data.result

        # 导出日志
        logs = AuditService.export_audit_logs(
            db,
            request_data.start_date,
            request_data.end_date,
            filters
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"成功导出 {len(logs)} 条审计日志",
                "data": {
                    "logs": logs,
                    "total": len(logs),
                    "start_date": request_data.start_date.isoformat(),
                    "end_date": request_data.end_date.isoformat()
                }
            }
        )

    except Exception as e:
        log.error(f"Failed to export audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出审计日志失败: {str(e)}")


@router.get("/statistics", response_model=AuditStatisticsResponse)
async def get_audit_statistics(
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """
    获取审计统计信息

    需要权限：audit:view
    """
    # 检查权限
    require_permission(current_user, Permission.AUDIT_VIEW)

    try:
        # 解析日期
        from datetime import datetime
        start_date_obj = None
        end_date_obj = None

        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="开始日期格式错误，应为 YYYY-MM-DD")

        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="结束日期格式错误，应为 YYYY-MM-DD")

        # 获取统计信息
        stats = AuditService.get_audit_statistics(db, start_date_obj, end_date_obj)

        return AuditStatisticsResponse(**stats)

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to get audit statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取审计统计失败: {str(e)}")
