from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.modules.publisher.services import publisher_service
from app.modules.publisher.schemas import (
    PublishRequest, BatchPublishRequest,
    PublishLogRead, PublishPoolRead,
    PublishResult, BatchPublishResult,
    RetryPublishRequest
)
from app.db.database import get_db
from app.core.permissions import require_permission, Permission
from app.modules.shared.deps import get_current_user

router = APIRouter(prefix="/publisher", tags=["publisher"])

@router.get("/history", response_model=list[PublishLogRead])
@require_permission(Permission.PUBLISHER_READ)
async def get_publish_history(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """获取发布历史"""
    return publisher_service.get_publish_history(db)

@router.get("/history/{id}", response_model=PublishLogRead)
@require_permission(Permission.PUBLISHER_READ)
async def get_publish_detail(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """获取发布详情"""
    log = publisher_service.get_publish_detail(db, id)
    if not log:
        raise HTTPException(status_code=404, detail="发布记录不存在")
    return log

@router.post("/publish", response_model=PublishResult)
@require_permission(Permission.PUBLISHER_EXECUTE)
async def manual_publish(request: PublishRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """手动发布"""
    result = publisher_service.manual_publish(db, request.dict())
    return result

@router.post("/retry/{id}", response_model=PublishResult)
@require_permission(Permission.PUBLISHER_EXECUTE)
async def retry_publish(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """重试发布"""
    result = publisher_service.retry_publish(db, id)
    return result

@router.post("/batch-publish", response_model=BatchPublishResult)
@require_permission(Permission.PUBLISHER_EXECUTE)
async def batch_publish(request: BatchPublishRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """批量发布"""
    result = publisher_service.batch_publish(db, request.dict())
    return result

@router.get("/pool", response_model=list[PublishPoolRead])
@require_permission(Permission.PUBLISHER_READ)
async def get_publish_pool(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """查看发布池"""
    return publisher_service.get_publish_pool(db)
