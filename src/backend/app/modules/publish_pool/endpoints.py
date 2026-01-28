from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.modules.publish_pool.services import publish_pool_manager_service
from app.modules.publish_pool.schemas import (
    AddToPoolRequest, UpdatePoolEntryRequest,
    PublishPoolRead, PublishPoolStatistics,
    PoolEntryStatusUpdate
)
from app.db.database import get_db

router = APIRouter(prefix="/publish-pool", tags=["publish-pool"])

@router.get("/", response_model=list[PublishPoolRead])
async def get_publish_pool(db: Session = Depends(get_db)):
    """获取发布池内容列表"""
    return publish_pool_manager_service.get_publish_pool(db)

@router.get("/{id}", response_model=PublishPoolRead)
async def get_pool_entry_detail(id: int, db: Session = Depends(get_db)):
    """获取发布池条目详情"""
    pool = db.query(PublishPool).filter(PublishPool.id == id).first()
    if not pool:
        raise HTTPException(status_code=404, detail="发布池条目不存在")
    return pool

@router.post("/", response_model=PublishPoolRead)
async def add_to_pool(request: AddToPoolRequest, db: Session = Depends(get_db)):
    """添加到发布池"""
    return publish_pool_manager_service.add_to_pool(
        db, request.content_id, request.priority, request.scheduled_at
    )

@router.delete("/{id}")
async def remove_from_pool(id: int, db: Session = Depends(get_db)):
    """从发布池移除"""
    success = publish_pool_manager_service.remove_from_pool(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="发布池条目不存在")
    return {"message": "已从发布池移除"}

@router.put("/{id}", response_model=PublishPoolRead)
async def update_pool_entry(id: int, request: UpdatePoolEntryRequest, db: Session = Depends(get_db)):
    """更新发布池条目"""
    updated = publish_pool_manager_service.update_pool_entry(db, id, request.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="发布池条目不存在")
    return updated

@router.post("/{id}/priority")
async def update_priority(id: int, priority: int, db: Session = Depends(get_db)):
    """调整发布优先级"""
    updated = publish_pool_manager_service.update_pool_entry(db, id, {"priority": priority})
    if not updated:
        raise HTTPException(status_code=404, detail="发布池条目不存在")
    return {"message": "优先级已更新"}

@router.get("/stats", response_model=PublishPoolStatistics)
async def get_pool_stats(db: Session = Depends(get_db)):
    """获取发布池统计"""
    return publish_pool_manager_service.get_pool_statistics(db)

@router.get("/pending", response_model=list[PublishPoolRead])
async def get_pending_entries(db: Session = Depends(get_db)):
    """获取待发布条目"""
    return publish_pool_manager_service.get_pending_entries(db)

@router.post("/{id}/start", response_model=PublishPoolRead)
async def start_publishing(id: int, db: Session = Depends(get_db)):
    """开始发布"""
    updated = publish_pool_manager_service.start_publishing(db, id)
    if not updated:
        raise HTTPException(status_code=404, detail="发布池条目不存在")
    return updated

@router.post("/{id}/complete", response_model=PublishPoolRead)
async def complete_publishing(id: int, published_log_id: int, db: Session = Depends(get_db)):
    """完成发布"""
    updated = publish_pool_manager_service.complete_publishing(db, id, published_log_id)
    if not updated:
        raise HTTPException(status_code=404, detail="发布池条目不存在")
    return updated

@router.post("/{id}/fail", response_model=PublishPoolRead)
async def fail_publishing(id: int, error_message: str, db: Session = Depends(get_db)):
    """发布失败"""
    updated = publish_pool_manager_service.fail_publishing(db, id, error_message)
    if not updated:
        raise HTTPException(status_code=404, detail="发布池条目不存在")
    return updated

@router.post("/{id}/retry", response_model=PublishPoolRead)
async def retry_publishing(id: int, db: Session = Depends(get_db)):
    """重试发布"""
    updated = publish_pool_manager_service.retry_publishing(db, id)
    if not updated:
        raise HTTPException(status_code=404, detail="发布池条目不存在")
    return updated
