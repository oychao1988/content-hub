"""
平台管理 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.modules.platform.services import platform_service
from app.modules.platform.schemas import (
    PlatformCreate, PlatformUpdate, PlatformResponse, PlatformListResponse
)
from app.db.database import get_db

router = APIRouter(tags=["platforms"])


@router.get("/", response_model=PlatformListResponse)
async def get_platforms(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """
    获取平台列表

    支持分页和搜索功能：
    - skip: 跳过的记录数（默认0）
    - limit: 返回的记录数（默认20，最大100）
    - search: 搜索关键词，会搜索平台名称、代码、类型
    """
    platforms, total = platform_service.get_all(db, skip=skip, limit=limit, search=search)
    return PlatformListResponse(items=platforms, total=total)


@router.get("/{platform_id}", response_model=PlatformResponse)
async def get_platform(platform_id: int, db: Session = Depends(get_db)):
    """
    获取平台详情

    Args:
        platform_id: 平台ID

    Returns:
        平台详情
    """
    platform = platform_service.get_by_id(db, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="平台不存在")
    return platform


@router.post("/", response_model=PlatformResponse, status_code=201)
async def create_platform(platform: PlatformCreate, db: Session = Depends(get_db)):
    """
    创建平台

    Args:
        platform: 平台创建数据

    Returns:
        创建的平台
    """
    # 检查平台名称是否已存在
    from app.models.platform import Platform
    existing = db.query(Platform).filter(Platform.name == platform.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="平台名称已存在")

    # 检查平台代码是否已存在
    existing_code = db.query(Platform).filter(Platform.code == platform.code).first()
    if existing_code:
        raise HTTPException(status_code=400, detail="平台代码已存在")

    return platform_service.create(db, platform.dict())


@router.put("/{platform_id}", response_model=PlatformResponse)
async def update_platform(
    platform_id: int,
    platform: PlatformUpdate,
    db: Session = Depends(get_db)
):
    """
    更新平台

    Args:
        platform_id: 平台ID
        platform: 平台更新数据

    Returns:
        更新后的平台
    """
    # 如果要更新名称，检查是否与其他平台冲突
    if platform.name is not None:
        from app.models.platform import Platform
        existing = db.query(Platform).filter(
            Platform.name == platform.name,
            Platform.id != platform_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="平台名称已被其他平台使用")

    # 如果要更新代码，检查是否与其他平台冲突
    if platform.code is not None:
        from app.models.platform import Platform
        existing_code = db.query(Platform).filter(
            Platform.code == platform.code,
            Platform.id != platform_id
        ).first()
        if existing_code:
            raise HTTPException(status_code=400, detail="平台代码已被其他平台使用")

    updated_platform = platform_service.update(
        db, platform_id, platform.dict(exclude_unset=True)
    )
    if not updated_platform:
        raise HTTPException(status_code=404, detail="平台不存在")
    return updated_platform


@router.delete("/{platform_id}")
async def delete_platform(platform_id: int, db: Session = Depends(get_db)):
    """
    删除平台

    Args:
        platform_id: 平台ID

    Returns:
        删除结果
    """
    success = platform_service.delete(db, platform_id)
    if not success:
        raise HTTPException(status_code=404, detail="平台不存在")
    return {"message": "平台已删除"}
