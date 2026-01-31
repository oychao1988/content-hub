from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.modules.content.services import content_service
from app.modules.content.schemas import (
    ContentCreateRequest, ContentUpdate, ContentRead, ContentListRead,
    SubmitReviewRequest, ApproveRequest, RejectRequest, ReviewStatistics,
    PaginatedContentList
)
from app.db.database import get_db
from app.core.permissions import require_permission, Permission
from app.modules.shared.deps import get_current_user

router = APIRouter(tags=["content"])

@router.get("/", response_model=PaginatedContentList)
@require_permission(Permission.CONTENT_READ)
async def get_content_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取内容列表（分页）"""
    return content_service.get_content_list(db, page, page_size)

@router.get("/{id}", response_model=ContentRead)
@require_permission(Permission.CONTENT_READ)
async def get_content_detail(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """获取内容详情"""
    content = content_service.get_content_detail(db, id)
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    return content

@router.post("/create", response_model=ContentRead)
@require_permission(Permission.CONTENT_CREATE)
async def create_content(request: ContentCreateRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """创建内容（调用 content-creator）"""
    try:
        return content_service.create_content(db, request.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{id}", response_model=ContentRead)
@require_permission(Permission.CONTENT_UPDATE)
async def update_content(id: int, content: ContentUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """更新内容"""
    updated_content = content_service.update_content(db, id, content.dict(exclude_unset=True))
    if not updated_content:
        raise HTTPException(status_code=404, detail="内容不存在")
    return updated_content

@router.delete("/{id}")
@require_permission(Permission.CONTENT_DELETE)
async def delete_content(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """删除内容"""
    success = content_service.delete_content(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="内容不存在")
    return {"message": "内容已删除"}

@router.post("/{id}/submit-review", response_model=ContentRead)
@require_permission(Permission.CONTENT_UPDATE)
async def submit_for_review(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """提交审核"""
    content = content_service.submit_for_review(db, id)
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    return content

@router.post("/{id}/approve", response_model=ContentRead)
@require_permission(Permission.CONTENT_PUBLISH)
async def approve_content(id: int, request: ApproveRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """审核通过"""
    content = content_service.approve_content(db, id, request.reviewer_id)
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    return content

@router.post("/{id}/reject", response_model=ContentRead)
@require_permission(Permission.CONTENT_PUBLISH)
async def reject_content(id: int, request: RejectRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """审核拒绝"""
    content = content_service.reject_content(db, id, request.reason, request.reviewer_id)
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    return content

@router.get("/review", response_model=list[ContentListRead])
@require_permission(Permission.CONTENT_PUBLISH)
async def get_pending_reviews(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """获取待审核列表"""
    return content_service.get_pending_reviews(db)

@router.get("/review/statistics", response_model=ReviewStatistics)
@require_permission(Permission.CONTENT_PUBLISH)
async def get_review_statistics(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """获取审核统计信息"""
    return content_service.get_review_statistics(db)
